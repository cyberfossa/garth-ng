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
        mp.addpart(
            name="file",
            filename=fname,
            data=fp.read(),
            content_type="application/octet-stream",
        )
        try:
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
        dir_path = os.path.expanduser(dir_path)
        os.makedirs(dir_path, exist_ok=True)
        if self.oauth2_token:
            with open(os.path.join(dir_path, OAUTH2_TOKEN_FILE), "w") as f:
                json.dump(asdict(self.oauth2_token), f, indent=4)

    def dumps(self) -> str:
        if self.oauth2_token:
            r = [asdict(self.oauth2_token)]
            s = json.dumps(r)
            return base64.b64encode(s.encode()).decode()

        raise GarthException(msg="No OAuth2Token available to serialize")

    def load(self, dir_path: str):
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
