from __future__ import annotations

from typing import TYPE_CHECKING

from ..exc import (
    AuthenticationError,
    CloudflareError,
    GarthException,
    MFARequiredError,
    NetworkError,
    RateLimitError,
)
from .state import MFAState
from .strategy import LoginResult, LoginStrategy
from .widget_strategy import WidgetStrategy


if TYPE_CHECKING:
    from curl_cffi.requests import Session

__all__ = [
    "STRATEGIES",
    "LoginStrategy",
    "LoginResult",
    "handle_mfa",
    "login",
]

STRATEGIES = [
    WidgetStrategy(),
]

_RETRYABLE = (RateLimitError, CloudflareError, NetworkError)


def login(
    session: Session,
    email: str,
    password: str,
    domain: str,
) -> LoginResult:
    """Try each strategy in order, return serviceTicketId.

    Retryable errors (rate-limit, Cloudflare, network) fall
    through to the next strategy. MFA and auth errors propagate
    immediately.
    """
    last_exc: Exception | None = None
    for strategy in STRATEGIES:
        try:
            return strategy.login(session, email, password, domain)
        except (MFARequiredError, AuthenticationError):
            raise
        except _RETRYABLE as exc:
            last_exc = exc
    raise GarthException(msg="All login strategies exhausted") from last_exc


def handle_mfa(
    session: Session,
    mfa_state: MFAState,
    mfa_code: str,
) -> LoginResult:
    """Dispatch MFA verification to the original strategy."""
    for strategy in STRATEGIES:
        if strategy.name == mfa_state.strategy_name:
            return strategy.handle_mfa(
                session,
                mfa_state.domain,
                mfa_state.state,
                mfa_code,
            )
    raise GarthException(msg=(f"Unknown strategy: {mfa_state.strategy_name}"))
