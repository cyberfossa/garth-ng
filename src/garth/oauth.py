from __future__ import annotations

import base64

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
        client_id=oauth2_token.client_id or DI_CLIENT_IDS[0],
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

    token_data = response.json()
    return OAuth2Token(**token_data, client_id=client_id)


def _build_basic_auth(client_id: str) -> str:
    return base64.b64encode(f"{client_id}:".encode()).decode()
