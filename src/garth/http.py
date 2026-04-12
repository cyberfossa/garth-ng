import base64
import json
import os
import time as _time
from collections.abc import Callable
from typing import IO, Any, cast, get_args
from urllib.parse import urljoin

from curl_cffi import CurlMime
from curl_cffi.requests import HttpMethod, Response, Session
from curl_cffi.requests.exceptions import RequestException
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import oauth, sso
from .auth_tokens import OAuth2Token
from .exc import GarthException, GarthHTTPError, MFARequiredError
from .sso.state import MFAState
from .telemetry import Telemetry
from .utils import asdict


USER_AGENT = {"User-Agent": "GCM-iOS-5.22.1.4"}
OAUTH1_TOKEN_FILE = "oauth1_token.json"
OAUTH2_TOKEN_FILE = "oauth2_token.json"

_SUPPORTED_METHODS: frozenset[str] = frozenset(get_args(HttpMethod))


class GarthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GARTH_")

    home: str | None = None
    token: str | None = None

    @model_validator(mode="after")
    def check_mutual_exclusivity(self):
        if self.home and self.token:
            raise GarthException(
                msg="GARTH_HOME and GARTH_TOKEN cannot both be set"
            )
        return self


class Client:
    """HTTP client for Garmin Connect API with OAuth2 authentication.

    Handles OAuth2 token management, session persistence, API requests
    with automatic token refresh, and MFA workflows. Create an instance
    directly or access the global `client` singleton.
    """

    session: Session
    last_resp: Response | None = None
    domain: str = "garmin.com"
    oauth2_token: OAuth2Token | None = None
    timeout: int = 10
    retries: int = 3
    status_forcelist: tuple[int, ...] = (408, 500, 502, 503, 504)
    backoff_factor: float = 0.5
    _user_profile: dict[str, Any] | None = None
    _garth_home: str | None = None
    telemetry: Telemetry

    def __init__(self, session: Session | None = None, **kwargs):
        """Initialize a new Client instance.

        Auto-resumes from GARTH_HOME or GARTH_TOKEN environment variables
        if set. Configures HTTP session, telemetry, and applies any
        configuration overrides via configure(**kwargs).

        Args:
            session: Optional pre-configured curl_cffi Session. If None,
                creates a new Session with chrome120 impersonation.
            **kwargs: Configuration parameters passed to configure()
                (timeout, retries, status_forcelist, backoff_factor,
                oauth2_token, domain, proxies, ssl_verify,
                telemetry_enabled, telemetry_send_to_logfire,
                telemetry_token, telemetry_callback).
        """
        self.session = (
            session
            if session is not None
            else Session(impersonate="chrome120")
        )
        self.session.headers.update(USER_AGENT)
        self.telemetry = Telemetry()
        self._auto_resume()
        self.configure(
            timeout=self.timeout,
            retries=self.retries,
            status_forcelist=self.status_forcelist,
            backoff_factor=self.backoff_factor,
            **kwargs,
        )
        if self.telemetry.enabled:
            print(f"Garth session: {self.telemetry.session_id}")

    def configure(
        self,
        /,
        oauth2_token: OAuth2Token | None = None,
        domain: str | None = None,
        proxies: dict[str, str] | None = None,
        ssl_verify: bool | None = None,
        timeout: int | None = None,
        retries: int | None = None,
        status_forcelist: tuple[int, ...] | None = None,
        backoff_factor: float | None = None,
        telemetry_enabled: bool | None = None,
        telemetry_send_to_logfire: bool | None = None,
        telemetry_token: str | None = None,
        telemetry_callback: Callable[[dict[str, Any]], None] | None = None,
    ):
        """Configure HTTP client and telemetry settings.

        All parameters are optional — only provided values are applied.
        Idempotent: safe to call multiple times.

        Args:
            oauth2_token: OAuth2 token for API authentication.
            domain: Garmin domain (default: "garmin.com", use "garmin.cn"
                for China region).
            proxies: Dictionary mapping scheme to proxy URL
                (e.g. {"https": "http://localhost:8888"}).
            ssl_verify: Enable/disable SSL certificate verification.
            timeout: HTTP request timeout in seconds.
            retries: Number of retry attempts for failed requests.
            status_forcelist: HTTP status codes triggering retries
                (default: 408, 500, 502, 503, 504).
            backoff_factor: Exponential backoff multiplier for retries
                (delays = backoff_factor * (2 ** attempt)).
            telemetry_enabled: Enable/disable OpenTelemetry collection.
            telemetry_send_to_logfire: Send telemetry to Logfire backend.
            telemetry_token: API token for Logfire telemetry service.
            telemetry_callback: Custom callback for telemetry events
                (called with event dict).
        """
        if oauth2_token is not None:
            self.oauth2_token = oauth2_token
        if domain:
            self.domain = domain
        if proxies is not None:
            self.session.proxies.update(cast(Any, proxies))
        if ssl_verify is not None:
            self.session.verify = ssl_verify
        if timeout is not None:
            self.timeout = timeout
        if retries is not None:
            self.retries = retries
        if status_forcelist is not None:
            self.status_forcelist = status_forcelist
        if backoff_factor is not None:
            self.backoff_factor = backoff_factor

        self.telemetry.configure(
            enabled=telemetry_enabled,
            send_to_logfire=telemetry_send_to_logfire,
            token=telemetry_token,
            callback=telemetry_callback,
        )

    def _auto_resume(self):
        """Auto-resume session from GARTH_HOME or GARTH_TOKEN env vars."""
        settings = GarthSettings()
        if settings.home:
            self._garth_home = settings.home
            oauth2_token_path = os.path.join(
                os.path.expanduser(settings.home), OAUTH2_TOKEN_FILE
            )
            oauth1_token_path = os.path.join(
                os.path.expanduser(settings.home), OAUTH1_TOKEN_FILE
            )
            if os.path.exists(oauth2_token_path) or os.path.exists(
                oauth1_token_path
            ):
                self.load(settings.home)
        elif settings.token:
            self.loads(settings.token)

    @property
    def user_profile(self):
        if not self._user_profile:
            result = self.connectapi("/userprofile-service/socialProfile")
            if not isinstance(result, dict):
                raise GarthException(msg="No profile from connectapi")
            self._user_profile = result
        return self._user_profile

    @property
    def profile(self):
        return self.user_profile

    @property
    def username(self):
        return self.user_profile["userName"]

    def request(
        self,
        method: str,
        subdomain: str,
        path: str,
        /,
        api: bool = False,
        referrer: str | bool = False,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> Response:
        """Make an HTTP request to a Garmin subdomain endpoint.

        When api=True, automatically handles OAuth2 token management:
        - Checks if access token has expired.
        - If expired but refresh token valid: calls refresh_token().
        - If neither valid: raises GarthException.
        - Adds Authorization header with token.

        Implements retry logic with exponential backoff:
        - Retries on status codes in status_forcelist.
        - Delays = backoff_factor * (2 ** attempt).
        - Default: 3 retries with 0.5x backoff on 408/5xx errors.

        Stores the response in self.last_resp for referrer chaining.
        Raises GarthHTTPError on non-2xx HTTP status codes.

        Args:
            method: HTTP method ("GET", "POST", "DELETE", "PUT", etc.).
            subdomain: Domain subdomain (e.g., "connectapi" for
                connectapi.garmin.com).
            path: Request path (e.g., "/wellness-service/...").
            api: If True, adds OAuth2 Authorization header and
                auto-refreshes token if needed. If False, no auth.
            referrer: If True, adds referer header from last_resp.url.
                If a string, uses that as the referer.
            headers: Additional headers (merged with defaults).
            **kwargs: Passed to curl_cffi Session.request() (data, json,
                multipart, params, cookies, etc.).

        Returns:
            Response: curl_cffi Response object (status, content,
                json(), etc.).

        Raises:
            GarthException: No valid token when api=True.
            GarthHTTPError: HTTP status indicates error.
        """
        method_upper = method.upper()
        if method_upper not in _SUPPORTED_METHODS:
            raise GarthException(msg=f"Unsupported HTTP method: {method}")
        http_method: HttpMethod = cast(HttpMethod, method_upper)
        request_headers = dict(headers) if headers else {}
        url = f"https://{subdomain}.{self.domain}"
        url = urljoin(url, path)
        if referrer is True and self.last_resp:
            request_headers["referer"] = self.last_resp.url
        if api:
            if self.oauth2_token is None or self.oauth2_token.expired:
                if self.oauth2_token and not self.oauth2_token.refresh_expired:
                    self.refresh_token()
                else:
                    raise GarthException(
                        msg="No valid OAuth2 token. Please login."
                    )
            request_headers["Authorization"] = str(self.oauth2_token)
        response: Response | None = None
        for attempt in range(self.retries + 1):
            response = self.session.request(
                http_method,
                url,
                headers=request_headers,
                timeout=self.timeout,
                **kwargs,
            )
            if response is None:
                continue
            if self.telemetry.enabled:
                self.telemetry.on_response(response)
            if response.status_code not in self.status_forcelist:
                break
            if attempt < self.retries:
                _time.sleep(self.backoff_factor * (2**attempt))

        if response is None:
            raise GarthException(msg="No response returned")
        self.last_resp = response
        try:
            self.last_resp.raise_for_status()
        except RequestException as e:
            raise GarthHTTPError(
                msg="Error in request",
                error=e,
            )
        return self.last_resp

    def get(self, *args, **kwargs) -> Response:
        return self.request("GET", *args, **kwargs)

    def post(self, *args, **kwargs) -> Response:
        return self.request("POST", *args, **kwargs)

    def delete(self, *args, **kwargs) -> Response:
        return self.request("DELETE", *args, **kwargs)

    def put(self, *args, **kwargs) -> Response:
        return self.request("PUT", *args, **kwargs)

    def login(
        self,
        email: str,
        password: str,
        *,
        prompt_mfa: Callable[[], str] | None = None,
        return_on_mfa: bool = False,
    ) -> OAuth2Token | MFAState:
        """Authenticate with Garmin using email and password.

        Handles three MFA workflows:
        1. No MFA required: returns OAuth2Token immediately.
        2. MFA required with return_on_mfa=True: returns MFAState
           (caller must call resume_login() with MFA code).
        3. MFA required with prompt_mfa provided: calls prompt_mfa(),
           sends MFA code, returns OAuth2Token.

        If MFA is required, no handler is provided, and return_on_mfa=False,
        raises MFARequiredError (caller must handle via except block).

        Automatically persists token to disk if GARTH_HOME env var was set
        or dump() was previously called.

        Args:
            email: Garmin account email.
            password: Garmin account password.
            prompt_mfa: Optional callback to prompt user for MFA code.
                Called if MFA required (takes no args, returns string).
            return_on_mfa: If True, returns MFAState when MFA required
                (instead of raising or calling prompt_mfa).

        Returns:
            OAuth2Token: Authenticated token (MFA not required or handled).
            MFAState: MFA state object (if return_on_mfa=True and MFA
                required).

        Raises:
            MFARequiredError: MFA required, return_on_mfa=False, and
                prompt_mfa is None. Must catch and call resume_login().
            GarthException: Login failed or invalid state during MFA.
        """
        try:
            result = sso.login(self.session, email, password, self.domain)
        except MFARequiredError as e:
            if return_on_mfa:
                if e.state is None:
                    raise GarthException(
                        msg="MFA required but state is missing"
                    )
                return e.state
            if prompt_mfa is None:
                raise
            mfa_code = prompt_mfa()
            if e.state is None:
                raise GarthException(msg="MFA required but state is missing")
            result = sso.handle_mfa(self.session, e.state, mfa_code)
        self.oauth2_token = oauth.exchange_service_ticket(
            self.session,
            result.ticket,
            result.service_url,
        )
        if self._garth_home:
            self.dump(self._garth_home)
        return self.oauth2_token

    def resume_login(self, mfa_state: MFAState, mfa_code: str) -> OAuth2Token:
        """Complete MFA challenge after receiving code from user.

        Call this after login() returns MFAState (when return_on_mfa=True)
        or after catching MFARequiredError. The MFA code comes from the user
        (typically via SMS or authenticator app).

        Automatically persists token to disk if GARTH_HOME env var was set
        or dump() was previously called.

        Args:
            mfa_state: MFA state object from login() or
                MFARequiredError.state.
            mfa_code: MFA code provided by user (usually 6-digit string).

        Returns:
            OAuth2Token: Authenticated token after MFA verification.

        Raises:
            GarthException: MFA code validation failed or invalid state.
        """
        result = sso.handle_mfa(self.session, mfa_state, mfa_code)
        self.oauth2_token = oauth.exchange_service_ticket(
            self.session,
            result.ticket,
            result.service_url,
        )
        if self._garth_home:
            self.dump(self._garth_home)
        return self.oauth2_token

    def refresh_token(self):
        """Refresh OAuth2 token using the refresh token.

        Called automatically by request() when the access token has
        expired but the refresh token is still valid (api=True). Can also
        be called manually to refresh before token expiry.

        Updates self.oauth2_token in-place with new access/refresh tokens
        and timestamps. Automatically persists the new token to disk if
        GARTH_HOME env var was set or dump() was previously called.

        Raises:
            GarthException: No OAuth2Token available or refresh token
                has expired.
        """
        if not self.oauth2_token:
            raise GarthException(msg="OAuth2Token required for refresh")
        self.oauth2_token = oauth.refresh_oauth2_token(
            self.session, self.oauth2_token
        )
        if self._garth_home:
            self.dump(self._garth_home)

    def connectapi(
        self, path: str, method="GET", **kwargs
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        resp = self.request(method, "connectapi", path, api=True, **kwargs)
        if resp.status_code == 204:
            return None
        return resp.json()

    def download(self, path: str, **kwargs) -> bytes:
        resp = self.get("connectapi", path, api=True, **kwargs)
        return resp.content

    def upload(
        self, fp: IO[bytes], /, path: str = "/upload-service/upload"
    ) -> dict[str, Any]:
        fname = os.path.basename(fp.name)
        mp = CurlMime()
        try:
            mp.addpart(
                name="file",
                filename=fname,
                data=fp.read(),
                content_type="application/octet-stream",
            )
            result = self.connectapi(
                path,
                method="POST",
                multipart=mp,
            )
        finally:
            mp.close()
        assert result is not None, "No result from upload"
        assert isinstance(result, dict)
        return result

    def dump(self, dir_path: str, /):
        """Persist OAuth2 token to disk as JSON file.

        Writes the token to dir_path/oauth2_token.json in JSON format
        (human-readable, 4-space indented). Creates dir_path if it
        doesn't exist.

        Also sets internal _garth_home so future login() and
        refresh_token() calls auto-persist their results to this
        directory.

        Args:
            dir_path: Directory to write token file to (created if
                needed).

        Raises:
            OSError: Cannot write to directory.
        """
        dir_path = os.path.expanduser(dir_path)
        os.makedirs(dir_path, exist_ok=True)
        if self.oauth2_token:
            with open(os.path.join(dir_path, OAUTH2_TOKEN_FILE), "w") as f:
                json.dump(asdict(self.oauth2_token), f, indent=4)

    def dumps(self) -> str:
        """Serialize OAuth2 token to base64-encoded string.

        Encodes the token as base64(JSON([{OAuth2Token fields}])), a
        JSON list with one dict element containing all token fields
        (access_token, refresh_token, expires_at,
        refresh_token_expires_at, etc.).

        Useful for storing tokens in environment variables (GARTH_TOKEN)
        or passing as CLI arguments.

        Returns:
            str: Base64-encoded JSON string.

        Raises:
            GarthException: No OAuth2Token available to serialize.
        """
        if self.oauth2_token:
            r = [asdict(self.oauth2_token)]
            s = json.dumps(r)
            return base64.b64encode(s.encode()).decode()

        raise GarthException(msg="No OAuth2Token available to serialize")

    def load(self, dir_path: str):
        """Load OAuth2 token from directory.

        Looks for dir_path/oauth2_token.json (preferred) or
        dir_path/oauth1_token.json (legacy). If neither exists, raises
        error.

        For legacy OAuth1 tokens, raises GarthException with migration
        instructions (user must re-authenticate with login()).

        Also sets internal _garth_home so future login() and
        refresh_token() calls auto-persist their results to this
        directory.

        Args:
            dir_path: Directory containing token file.

        Raises:
            GarthException: No oauth2_token.json found, or legacy OAuth1
                token detected (with re-auth instructions in error).
        """
        dir_path = os.path.expanduser(dir_path)
        oauth2_path = os.path.join(dir_path, OAUTH2_TOKEN_FILE)
        oauth1_path = os.path.join(dir_path, OAUTH1_TOKEN_FILE)

        if os.path.exists(oauth2_path):
            with open(oauth2_path) as f:
                self.oauth2_token = OAuth2Token(**json.load(f))
        elif os.path.exists(oauth1_path):
            raise GarthException(
                msg=(
                    "Legacy OAuth1 tokens found. "
                    "Please re-authenticate with garth.login()"
                )
            )
        else:
            raise GarthException(
                msg=(
                    f"No token files found in {dir_path}. "
                    "Please login with garth.login() first."
                )
            )

    def loads(self, s: str):
        """Deserialize OAuth2 token from base64-encoded string.

        Decodes the base64 string and validates the format:
        - Must be a JSON list with exactly 1 element (a dict).
        - Dict must contain "access_token" field.
        - Legacy 2-element list format (OAuth1) raises error with
          migration instructions.

        Args:
            s: Base64-encoded token string (from dumps() or GARTH_TOKEN
                env).

        Raises:
            GarthException: Invalid format, legacy OAuth1 token, or decode
                failure.
        """
        data = json.loads(base64.b64decode(s))
        if (
            isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], dict)
            and "access_token" in data[0]
        ):
            self.oauth2_token = OAuth2Token(**data[0])
            return

        if isinstance(data, list) and len(data) == 2:
            raise GarthException(
                msg=(
                    "Legacy token format. "
                    "Please re-authenticate with garth.login()"
                )
            )

        raise GarthException(msg="Unsupported token format")


client = Client()
