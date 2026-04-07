from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Protocol, runtime_checkable


if TYPE_CHECKING:
    from curl_cffi.requests import Session


class LoginResult(NamedTuple):
    ticket: str
    service_url: str


@runtime_checkable
class LoginStrategy(Protocol):
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
