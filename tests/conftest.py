import os
import sys
import time
from pathlib import Path


os.environ["GARTH_TELEMETRY_ENABLED"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from curl_cffi.requests import Session

from garth.auth_tokens import OAuth2Token
from garth.http import Client
from tests.helpers import setup_cassette


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
def oauth2_token() -> OAuth2Token:
    return OAuth2Token(
        access_token="bar",
        refresh_token="baz",
        expires_in=3599,
        expires_at=time.time() + 3599,
        refresh_token_expires_in=7199,
        refresh_token_expires_at=time.time() + 7199,
        scope="CONNECT_READ CONNECT_WRITE",
        jti="foo",
    )


@pytest.fixture
def authed_client(oauth2_token: OAuth2Token) -> Client:
    client = Client()
    client.oauth2_token = oauth2_token
    client._garth_home = None
    assert client.oauth2_token and isinstance(client.oauth2_token, OAuth2Token)
    assert not client.oauth2_token.expired
    return client


@pytest.fixture
def load_cassette():
    return setup_cassette
