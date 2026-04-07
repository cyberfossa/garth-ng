from __future__ import annotations

import base64
import json
import time
from typing import cast

from curl_cffi.requests import Session
from curl_cffi.requests.exceptions import RequestException

from .auth_tokens import OAuth2Token
from .exc import GarthHTTPError


DI_TOKEN_URL = "https://diauth.garmin.com/di-oauth2-service/oauth/token"
DI_CLIENT_IDS = [
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI_2024Q4",
    "GARMIN_CONNECT_MOBILE_ANDROID_DI",
]
DI_GRANT_TYPE_TICKET = (
    "https://connectapi.garmin.com/"
    "di-oauth2-service/oauth/grant/service_ticket"
)
DI_GRANT_TYPE_REFRESH = "refresh_token"


def exchange_service_ticket(
    session: Session, ticket: str, service_url: str
) -> OAuth2Token:
    last_error = None
    for client_id in DI_CLIENT_IDS:
        try:
            return _do_exchange(
                session,
                client_id=client_id,
                grant_type=DI_GRANT_TYPE_TICKET,
                extra_params={
                    "service_ticket": ticket,
                    "service_url": service_url,
                },
            )
        except GarthHTTPError as error:
            last_error = error
            continue

    if last_error is None:
        raise AssertionError("DI_CLIENT_IDS must contain at least one item")
    raise last_error


def refresh_oauth2_token(
    session: Session, oauth2_token: OAuth2Token
) -> OAuth2Token:
    return _do_exchange(
        session,
        client_id=DI_CLIENT_IDS[0],
        grant_type=DI_GRANT_TYPE_REFRESH,
        extra_params={"refresh_token": oauth2_token.refresh_token},
    )


def _do_exchange(
    session: Session,
    *,
    client_id: str,
    grant_type: str,
    extra_params: dict[str, str],
) -> OAuth2Token:
    auth = _build_basic_auth(client_id)
    data = {
        "grant_type": grant_type,
        "client_id": client_id,
        **extra_params,
    }
    try:
        response = session.post(
            DI_TOKEN_URL,
            data=data,
            headers={
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                "Authorization": f"Basic {auth}",
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response.raise_for_status()
    except RequestException as error:
        raise GarthHTTPError(
            msg="DI-OAuth2 exchange failed",
            error=error,
        ) from error

    token_data = cast(dict[str, object], json.loads(response.content))
    now = time.time()
    expires_in = _as_int(token_data.get("expires_in"), default=0)
    expires_at = now + expires_in
    refresh_expires_in_raw = token_data.get("refresh_token_expires_in")
    refresh_expires_in = (
        _as_int(refresh_expires_in_raw)
        if refresh_expires_in_raw is not None
        else None
    )
    refresh_expires_at = (
        now + refresh_expires_in if refresh_expires_in is not None else None
    )
    access_token = _as_str(token_data["access_token"])
    refresh_token = _as_str(token_data["refresh_token"])
    token_type = _as_str(token_data.get("token_type", "Bearer"))
    scope_raw = token_data.get("scope")
    scope = _as_str(scope_raw) if scope_raw is not None else None
    jti_raw = token_data.get("jti")
    jti = _as_str(jti_raw) if jti_raw is not None else None
    mfa_token_raw = token_data.get("mfa_token")
    mfa_token = _as_str(mfa_token_raw) if mfa_token_raw is not None else None
    mfa_ts_raw = token_data.get("mfa_expiration_timestamp")
    mfa_ts = _as_str(mfa_ts_raw) if mfa_ts_raw is not None else None
    mfa_ms_raw = token_data.get("mfa_expiration_timestamp_millis")
    mfa_ms = _as_int(mfa_ms_raw) if mfa_ms_raw is not None else None
    return OAuth2Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        expires_in=expires_in,
        expires_at=expires_at,
        refresh_token_expires_in=refresh_expires_in,
        refresh_token_expires_at=refresh_expires_at,
        scope=scope,
        jti=jti,
        mfa_token=mfa_token,
        mfa_expiration_timestamp=mfa_ts,
        mfa_expiration_timestamp_millis=mfa_ms,
    )


def _build_basic_auth(client_id: str) -> str:
    return base64.b64encode(f"{client_id}:".encode()).decode()


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore
    except (TypeError, ValueError):
        return default


def _as_str(value: object) -> str:
    if isinstance(value, str):
        return value
    return str(value)
