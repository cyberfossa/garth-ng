import base64
import json
import tempfile
import time

import pytest

from garth.auth_tokens import OAuth2Token
from garth.storage import EnvTokenStorage, FileTokenStorage


@pytest.fixture
def sample_token() -> OAuth2Token:
    return OAuth2Token(
        access_token="access-abc",
        refresh_token="refresh-xyz",
        expires_in=3600,
        expires_at=time.time() + 3600,
        refresh_token_expires_in=7200,
        refresh_token_expires_at=time.time() + 7200,
        scope="CONNECT_READ CONNECT_WRITE",
        jti="jti-123",
        client_id="MY_CLIENT_ID",
    )


def test_file_token_storage_roundtrip(sample_token: OAuth2Token):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileTokenStorage(tmpdir)
        storage.save(sample_token)
        loaded = storage.load()

        assert loaded is not None
        assert loaded.access_token == sample_token.access_token
        assert loaded.refresh_token == sample_token.refresh_token
        assert loaded.client_id == sample_token.client_id
        assert loaded.scope == sample_token.scope


def test_file_token_storage_missing_returns_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileTokenStorage(tmpdir)
        assert storage.load() is None


def test_env_token_storage_load(
    sample_token: OAuth2Token, monkeypatch: pytest.MonkeyPatch
):
    from garth.utils import asdict

    token_data = [asdict(sample_token)]
    encoded = base64.b64encode(json.dumps(token_data).encode()).decode()
    monkeypatch.setenv("GARTH_TOKEN", encoded)

    storage = EnvTokenStorage()
    loaded = storage.load()

    assert loaded is not None
    assert loaded.access_token == sample_token.access_token
    assert loaded.refresh_token == sample_token.refresh_token


def test_env_token_storage_save_is_noop(sample_token: OAuth2Token):
    storage = EnvTokenStorage()
    storage.save(sample_token)


def test_env_token_storage_load_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GARTH_TOKEN", raising=False)
    storage = EnvTokenStorage()
    assert storage.load() is None


def test_file_token_storage_expands_user():
    storage = FileTokenStorage("~/some/path")
    assert "~" not in str(storage.path)
