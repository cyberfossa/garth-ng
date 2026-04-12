from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Protocol, runtime_checkable


if TYPE_CHECKING:
    from curl_cffi.requests import Session


class LoginResult(NamedTuple):
    """OAuth2 service ticket and URL for token exchange.

    Returned by LoginStrategy.login() and LoginStrategy.handle_mfa() to
    provide the credentials needed to exchange with Garmin's OAuth2 endpoint
    for an access token.

    Attributes:
        ticket: Service ticket ID.
        service_url: URL to which the ticket should be presented.
    """

    ticket: str
    service_url: str


@runtime_checkable
class LoginStrategy(Protocol):
    """Protocol for Garmin SSO login strategies.

    Implementations provide different methods to authenticate with Garmin's
    SSO system (e.g., widget-based login). Each strategy must support both
    initial login and MFA completion flows.
    """

    @property
    def name(self) -> str: ...

    def login(
        self,
        session: Session,
        email: str,
        password: str,
        domain: str,
    ) -> LoginResult:
        """Perform login, return serviceTicketId."""
        ...

    def handle_mfa(
        self,
        session: Session,
        domain: str,
        state: dict[str, object],
        mfa_code: str,
    ) -> LoginResult:
        """Complete MFA, return serviceTicketId."""
        ...
