from unittest.mock import patch

import pytest

from garth.auth_tokens import OAuth2Token
from garth.exc import GarthException
from garth.http import Client
from garth.sso.state import MFAChallenge, MFAState


@pytest.fixture
def mfa_state() -> MFAState:
    return MFAState(
        strategy_name="widget",
        domain="garmin.com",
        state={"ticket": "ST-123"},
    )


@pytest.fixture
def mfa_challenge(mfa_state: MFAState) -> MFAChallenge:
    return MFAChallenge(
        mfa_state=mfa_state,
        cookies={"GARMIN-SSO": "abc123", "SESSIONID": "xyz789"},
    )


def test_mfa_challenge_json_roundtrip(mfa_challenge: MFAChallenge):
    json_str = mfa_challenge.to_json()
    restored = MFAChallenge.from_json(json_str)
    assert restored.mfa_state.strategy_name == "widget"
    assert restored.mfa_state.domain == "garmin.com"
    assert restored.mfa_state.state == {"ticket": "ST-123"}
    assert restored.cookies == {"GARMIN-SSO": "abc123", "SESSIONID": "xyz789"}


def test_login_mfa_challenge_returns_challenge(
    client: Client, mfa_state: MFAState
):
    client.session.cookies.set("GARMIN-SSO", "abc123")
    with patch.object(client, "login", return_value=mfa_state):
        challenge = client.login_mfa_challenge("a@b.com", "pass")
    assert challenge.mfa_state is mfa_state
    assert "GARMIN-SSO" in challenge.cookies


def test_login_mfa_challenge_raises_when_no_mfa(
    client: Client, oauth2_token: OAuth2Token
):
    with patch.object(client, "login", return_value=oauth2_token):
        with pytest.raises(GarthException, match="MFA was not required"):
            client.login_mfa_challenge("a@b.com", "pass")


def test_resume_mfa_restores_cookies_and_returns_token(
    client: Client, mfa_challenge: MFAChallenge, oauth2_token: OAuth2Token
):
    with patch.object(
        client, "resume_login", return_value=oauth2_token
    ) as mock_resume:
        result = client.resume_mfa(mfa_challenge, "123456")

    assert result is oauth2_token
    mock_resume.assert_called_once_with(mfa_challenge.mfa_state, "123456")
    # Verify cookies were restored
    assert client.session.cookies.get("GARMIN-SSO") == "abc123"
    assert client.session.cookies.get("SESSIONID") == "xyz789"
