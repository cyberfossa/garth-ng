from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from curl_cffi.requests.exceptions import RequestException


if TYPE_CHECKING:
    from garth.sso.state import MFAState


@dataclass
class GarthException(Exception):
    """Base exception for all garth exceptions."""

    msg: str

    def __str__(self) -> str:
        return self.msg


@dataclass
class GarthHTTPError(GarthException):
    """Raised when an HTTP request returns a non-success status (4xx/5xx).

    Wraps the `RequestException` from `raise_for_status()` in the `error`
    field. For transport-layer failures (DNS, timeouts), see `NetworkError`.
    """

    error: RequestException

    def __str__(self) -> str:
        return f"{self.msg}: {self.error}"


@dataclass
class RateLimitError(GarthException):
    """Raised when Garmin's API returns a rate-limit response.

    This is a retryable error — the request can be retried after a delay.
    """

    pass


@dataclass
class CloudflareError(GarthException):
    """Raised when a Cloudflare protection page blocks the request.

    This is a retryable error — the request can be retried after a delay.
    """

    pass


@dataclass
class NetworkError(GarthException):
    """Raised on connection failures (DNS errors, timeouts, network resets).

    This is a retryable error — the request can be retried after a delay.
    The underlying error is captured in the `error` field when available.
    """

    error: RequestException | None = None


@dataclass
class AuthenticationError(GarthException):
    """Raised when login credentials are invalid.

    This error indicates authentication failure (bad email/password or
    disabled account). It is not retryable.
    """

    pass


@dataclass
class MFARequiredError(GarthException):
    """Raised when MFA is required during login but no handler was provided.

    The `state` field contains the MFAState needed to complete authentication
    via Client.resume_login() after the user has provided their MFA code.
    """

    state: MFAState | None = None
