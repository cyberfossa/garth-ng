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
    error: RequestException

    def __str__(self) -> str:
        return f"{self.msg}: {self.error}"


@dataclass
class RateLimitError(GarthException):
    pass


@dataclass
class CloudflareError(GarthException):
    pass


@dataclass
class NetworkError(GarthException):
    error: RequestException | None = None


@dataclass
class AuthenticationError(GarthException):
    pass


@dataclass
class MFARequiredError(GarthException):
    state: MFAState | None = None
