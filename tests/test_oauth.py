from typing import cast

import pytest
from _pytest.monkeypatch import MonkeyPatch
from curl_cffi.requests import Session
from curl_cffi.requests.exceptions import RequestException

from garth.auth_tokens import OAuth2Token
from garth.exc import GarthHTTPError
from garth.oauth import (
    DI_CLIENT_IDS,
    DI_GRANT_TYPE_REFRESH,
    DI_GRANT_TYPE_TICKET,
    _as_int,
    _build_basic_auth,
    exchange_service_ticket,
    refresh_oauth2_token,
)


def make_token_payload(
    *,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    token_type: str = "Bearer",
    refresh_expires_in: int | None = None,
    scope: str | None = None,
    jti: str | None = None,
    mfa_token: str | None = None,
    mfa_expiration_timestamp: str | None = None,
    mfa_expiration_timestamp_millis: int | None = None,
) -> bytes:
    payload_parts = [
        f'"access_token":"{access_token}"',
        f'"refresh_token":"{refresh_token}"',
        f'"token_type":"{token_type}"',
        f'"expires_in":{expires_in}',
    ]
    if refresh_expires_in is not None:
        payload_parts.append(
            f'"refresh_token_expires_in":{refresh_expires_in}'
        )
    if scope is not None:
        payload_parts.append(f'"scope":"{scope}"')
    if jti is not None:
        payload_parts.append(f'"jti":"{jti}"')
    if mfa_token is not None:
        payload_parts.append(f'"mfa_token":"{mfa_token}"')
    if mfa_expiration_timestamp is not None:
        payload_parts.append(
            f'"mfa_expiration_timestamp":"{mfa_expiration_timestamp}"'
        )
    if mfa_expiration_timestamp_millis is not None:
        payload_parts.append(
            f'"mfa_expiration_timestamp_millis":{mfa_expiration_timestamp_millis}'
        )
    return ("{" + ",".join(payload_parts) + "}").encode()


class FakeResponse:
    content: bytes
    _error: RequestException | None
    status_code: int
    text: str

    def __init__(
        self,
        *,
        content: bytes,
        error: RequestException | None = None,
    ) -> None:
        self.content = content
        self._error = error
        self.status_code = 200
        self.text = content.decode("utf-8", errors="replace")

    def raise_for_status(self) -> None:
        if self._error is not None:
            raise self._error


class FakeSession:
    _responses: list[FakeResponse]
    calls: list[dict[str, object]]

    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = responses
        self.calls = []

    def post(
        self,
        _url: str,
        *,
        data: dict[str, str],
        headers: dict[str, str],
    ) -> FakeResponse:
        self.calls.append({"data": data, "headers": headers})
        return self._responses.pop(0)


def test_exchange_service_ticket_success():
    response = FakeResponse(
        content=make_token_payload(
            access_token="access-123",
            refresh_token="refresh-123",
            expires_in=3600,
            refresh_expires_in=7200,
            scope="read",
            jti="token-jti",
            mfa_token="mfa-123",
            mfa_expiration_timestamp="2026-01-01T00:00:00.000Z",
            mfa_expiration_timestamp_millis=1767225600000,
        )
    )
    session = FakeSession([response])

    token = exchange_service_ticket(
        cast(Session, cast(object, session)),
        "ST-abc",
        "https://sso.garmin.com/sso/embed",
    )

    assert isinstance(token, OAuth2Token)
    assert token.access_token == "access-123"
    assert token.refresh_token == "refresh-123"
    assert token.expires_in == 3600
    assert token.scope == "read"
    assert token.jti == "token-jti"
    assert token.mfa_token == "mfa-123"
    assert token.mfa_expiration_timestamp == "2026-01-01T00:00:00.000Z"
    assert token.mfa_expiration_timestamp_millis == 1767225600000
    assert token.expires_at is not None
    assert token.refresh_token_expires_at is not None
    assert token.expires_at > 0
    assert token.refresh_token_expires_at > token.expires_at

    assert len(session.calls) == 1
    call_data = session.calls[0]["data"]
    assert isinstance(call_data, dict)
    assert call_data["grant_type"] == DI_GRANT_TYPE_TICKET
    assert call_data["service_ticket"] == "ST-abc"
    assert call_data["service_url"] == "https://sso.garmin.com/sso/embed"
    assert call_data["client_id"] == DI_CLIENT_IDS[0]
    call_headers = session.calls[0]["headers"]
    assert isinstance(call_headers, dict)
    assert (
        call_headers["Accept"] == "application/json,text/html;q=0.9,*/*;q=0.8"
    )
    assert call_headers["Cache-Control"] == "no-cache"


def test_exchange_invalid_ticket():
    responses = [
        FakeResponse(
            content=b"{}",
            error=RequestException("bad ticket"),
        )
        for _ in range(len(DI_CLIENT_IDS))
    ]
    session = FakeSession(responses)

    with pytest.raises(GarthHTTPError):
        _ = exchange_service_ticket(
            cast(Session, cast(object, session)),
            "ST-invalid",
            "https://sso.garmin.com/sso/embed",
        )


def test_refresh_oauth2_token():
    response = FakeResponse(
        content=make_token_payload(
            access_token="access-new",
            refresh_token="refresh-new",
            expires_in=1800,
        )
    )
    session = FakeSession([response])
    old_token = OAuth2Token(
        access_token="access-old",
        refresh_token="refresh-old",
        expires_in=3600,
    )

    new_token = refresh_oauth2_token(
        cast(Session, cast(object, session)),
        old_token,
    )

    assert isinstance(new_token, OAuth2Token)
    assert new_token.access_token == "access-new"
    assert new_token.refresh_token == "refresh-new"
    assert new_token.expires_in == 1800

    call_data = session.calls[0]["data"]
    assert isinstance(call_data, dict)
    assert call_data["grant_type"] == DI_GRANT_TYPE_REFRESH
    assert call_data["refresh_token"] == "refresh-old"
    assert call_data["client_id"] == DI_CLIENT_IDS[0]


def test_build_basic_auth():
    auth = _build_basic_auth("client:id")
    assert auth == "Y2xpZW50OmlkOg=="


def test_exchange_refresh_expires_in_zero():
    response = FakeResponse(
        content=make_token_payload(
            access_token="access-xyz",
            refresh_token="refresh-xyz",
            expires_in=3600,
            refresh_expires_in=0,
        )
    )
    session = FakeSession([response])

    token = exchange_service_ticket(
        cast(Session, cast(object, session)),
        "ST-abc",
        "https://sso.garmin.com/sso/embed",
    )

    assert token.refresh_token_expires_at is not None
    assert token.refresh_token_expires_in == 0


def test_exchange_tries_all_client_ids(monkeypatch: MonkeyPatch):
    first = FakeResponse(
        content=b"{}",
        error=RequestException("first failed"),
    )
    second = FakeResponse(
        content=make_token_payload(
            access_token="access-fallback",
            refresh_token="refresh-fallback",
            expires_in=600,
        )
    )
    session = FakeSession([first, second])
    monkeypatch.setattr(
        "garth.oauth.DI_CLIENT_IDS",
        ["GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2", "FALLBACK_CLIENT_ID"],
    )

    token = exchange_service_ticket(
        cast(Session, cast(object, session)),
        "ST-fallback",
        "https://sso.garmin.com/sso/embed",
    )

    assert token.access_token == "access-fallback"
    assert len(session.calls) == 2
    first_call_data = session.calls[0]["data"]
    second_call_data = session.calls[1]["data"]
    assert isinstance(first_call_data, dict)
    assert isinstance(second_call_data, dict)
    assert (
        first_call_data["client_id"]
        == "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2"
    )
    assert second_call_data["client_id"] == "FALLBACK_CLIENT_ID"


def test_as_int_returns_default_for_non_numeric_string():
    assert _as_int("never") == 0
    assert _as_int("never", default=42) == 42


def test_as_int_returns_default_for_empty_string():
    assert _as_int("") == 0
