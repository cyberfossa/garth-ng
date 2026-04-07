import os
import sys
import time
from pathlib import Path


os.environ["GARTH_TELEMETRY_ENABLED"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from helpers import setup_cassette
from requests import Session

from garth.auth_tokens import OAuth1Token, OAuth2Token
from garth.http import Client


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.setenv("GARTH_TELEMETRY_ENABLED", "false")
    monkeypatch.delenv("GARTH_HOME", raising=False)
    monkeypatch.delenv("GARTH_TOKEN", raising=False)


@pytest.fixture
def session():
    return Session()


@pytest.fixture
def client(session, monkeypatch) -> Client:
    monkeypatch.delenv("GARTH_HOME", raising=False)
    monkeypatch.delenv("GARTH_TOKEN", raising=False)
    return Client(session=session)


@pytest.fixture
def oauth1_token_dict() -> dict:
    return dict(
        oauth_token="7fdff19aa9d64dda83e9d7858473aed1",
        oauth_token_secret="49919d7c4c8241ac93fb4345886fbcea",
        mfa_token="ab316f8640f3491f999f3298f3d6f1bb",
        mfa_expiration_timestamp="2024-08-02 05:56:10.000",
        domain="garmin.com",
    )


@pytest.fixture
def oauth1_token(oauth1_token_dict) -> OAuth1Token:
    return OAuth1Token(**oauth1_token_dict)


@pytest.fixture
def oauth2_token_dict() -> dict:
    return dict(
        scope="CONNECT_READ CONNECT_WRITE",
        jti="foo",
        token_type="Bearer",
        access_token="bar",
        refresh_token="baz",
        expires_in=3599,
        refresh_token_expires_in=7199,
    )


@pytest.fixture
def oauth2_token(oauth2_token_dict: dict) -> OAuth2Token:
    token = OAuth2Token(
        expires_at=int(time.time() + 3599),
        refresh_token_expires_at=int(time.time() + 7199),
        **oauth2_token_dict,
    )
    return token


@pytest.fixture
def authed_client(
    oauth1_token: OAuth1Token,
    oauth2_token: OAuth2Token,
) -> Client:
    client = Client()
    client.configure(oauth1_token=oauth1_token, oauth2_token=oauth2_token)
    client._garth_home = None
    assert client.oauth2_token and isinstance(client.oauth2_token, OAuth2Token)
    assert not client.oauth2_token.expired
    return client


@pytest.fixture
def load_cassette():
    return setup_cassette
