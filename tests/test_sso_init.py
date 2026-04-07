from __future__ import annotations

from typing import cast
from unittest.mock import MagicMock

import pytest

from garth.exc import (
    AuthenticationError,
    CloudflareError,
    GarthException,
    MFARequiredError,
    RateLimitError,
)
from garth.sso import STRATEGIES
from garth.sso.state import MFAState
from garth.sso.strategy import LoginResult, LoginStrategy


def _make_strategy(
    name: str,
    login_effect: BaseException | None = None,
    login_return: LoginResult | None = None,
) -> LoginStrategy:
    s = MagicMock()
    s.name = name
    if login_effect is not None:
        cast(MagicMock, s.login).side_effect = login_effect
    elif login_return is not None:
        cast(MagicMock, s.login).return_value = login_return
    return s


def _run_login(strategies: list[LoginStrategy]) -> LoginResult:
    from garth.sso import login as _login

    session = MagicMock()
    import garth.sso as sso_mod

    original = sso_mod.STRATEGIES
    sso_mod.STRATEGIES = strategies  # type: ignore[assignment]
    try:
        return _login(
            session,
            email="u@example.com",
            password="pw",
            domain="garmin.com",
        )
    finally:
        sso_mod.STRATEGIES = original


def test_strategies_order():
    names = [s.name for s in STRATEGIES]
    assert names == ["widget"]


def test_fallback_rate_limit():
    s1 = _make_strategy(
        "portal",
        login_effect=RateLimitError(msg="429"),
    )
    s2 = _make_strategy(
        "widget",
        login_return=LoginResult("ST-OK", "https://sso.garmin.com/sso/embed"),
    )
    s3 = _make_strategy("mobile")

    result = _run_login([s1, s2, s3])

    assert result == LoginResult("ST-OK", "https://sso.garmin.com/sso/embed")
    cast(MagicMock, s1.login).assert_called_once()
    cast(MagicMock, s2.login).assert_called_once()
    cast(MagicMock, s3.login).assert_not_called()


def test_fallback_cloudflare():
    s1 = _make_strategy(
        "portal",
        login_effect=CloudflareError(msg="cf1"),
    )
    s2 = _make_strategy(
        "widget",
        login_effect=CloudflareError(msg="cf2"),
    )
    s3 = _make_strategy(
        "mobile",
        login_return=LoginResult(
            "ST-3",
            "https://mobile.integration.garmin.com/gcm/android",
        ),
    )

    result = _run_login([s1, s2, s3])

    assert result == LoginResult(
        "ST-3",
        "https://mobile.integration.garmin.com/gcm/android",
    )
    cast(MagicMock, s1.login).assert_called_once()
    cast(MagicMock, s2.login).assert_called_once()
    cast(MagicMock, s3.login).assert_called_once()


def test_all_fail():
    strategies: list[LoginStrategy] = [
        _make_strategy(
            name,
            login_effect=CloudflareError(msg="cf"),
        )
        for name in ("portal", "widget", "mobile")
    ]

    with pytest.raises(GarthException, match="exhausted"):
        _ = _run_login(strategies)


def test_mfa_not_caught():
    mfa_state = MFAState(
        strategy_name="portal",
        domain="garmin.com",
        state={},
    )
    s1 = _make_strategy(
        "portal",
        login_effect=MFARequiredError(msg="MFA", state=mfa_state),
    )
    s2 = _make_strategy(
        "widget",
        login_return=LoginResult(
            "ST-NOPE",
            "https://sso.garmin.com/sso/embed",
        ),
    )

    with pytest.raises(MFARequiredError):
        _ = _run_login([s1, s2])

    cast(MagicMock, s2.login).assert_not_called()


def test_auth_error_not_caught():
    s1 = _make_strategy(
        "portal",
        login_effect=AuthenticationError(msg="bad creds"),
    )
    s2 = _make_strategy(
        "widget",
        login_return=LoginResult(
            "ST-NOPE",
            "https://sso.garmin.com/sso/embed",
        ),
    )

    with pytest.raises(AuthenticationError):
        _ = _run_login([s1, s2])

    cast(MagicMock, s2.login).assert_not_called()


def test_handle_mfa_dispatches():
    import garth.sso as sso_mod
    from garth.sso import handle_mfa

    s1 = MagicMock()
    s1.name = "portal"

    s2 = MagicMock()
    s2.name = "widget"
    cast(MagicMock, s2.handle_mfa).return_value = LoginResult(
        "ST-MFA-OK",
        "https://connect.garmin.com/app",
    )

    original = sso_mod.STRATEGIES
    sso_mod.STRATEGIES = [s1, s2]  # type: ignore[assignment]
    try:
        mfa_state = MFAState(
            strategy_name="widget",
            domain="garmin.com",
            state={"mfa_url": "https://example.com"},
        )
        result = handle_mfa(MagicMock(), mfa_state, "123456")
    finally:
        sso_mod.STRATEGIES = original

    assert result == LoginResult("ST-MFA-OK", "https://connect.garmin.com/app")
    cast(MagicMock, s1.handle_mfa).assert_not_called()
    cast(MagicMock, s2.handle_mfa).assert_called_once()


def test_handle_mfa_unknown_strategy():
    import garth.sso as sso_mod
    from garth.sso import handle_mfa

    original = sso_mod.STRATEGIES
    sso_mod.STRATEGIES = []  # type: ignore[assignment]
    try:
        mfa_state = MFAState(
            strategy_name="unknown",
            domain="garmin.com",
            state={},
        )
        with pytest.raises(GarthException, match="Unknown strategy"):
            _ = handle_mfa(MagicMock(), mfa_state, "000000")
    finally:
        sso_mod.STRATEGIES = original
