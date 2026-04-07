from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from curl_cffi.requests import Session


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
    ) -> str:
        """Perform login, return serviceTicketId."""
        ...

    def handle_mfa(
        self,
        session: Session,
        domain: str,
        state: dict[str, Any],
        mfa_code: str,
    ) -> str:
        """Complete MFA, return serviceTicketId."""
        ...
