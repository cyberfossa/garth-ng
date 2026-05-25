from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Protocol, TypedDict, cast

from typing_extensions import Required

from .auth_tokens import OAuth2Token
from .utils import asdict


OAUTH2_TOKEN_FILE = "oauth2_token.json"


class _TokenData(TypedDict, total=False):
    access_token: Required[str]
    refresh_token: Required[str]
    expires_in: Required[int]
    token_type: str
    expires_at: float | None
    refresh_token_expires_in: int | None
    refresh_token_expires_at: float | None
    scope: str | None
    jti: str | None
    client_id: str | None


class TokenStorage(Protocol):
    def save(self, token: OAuth2Token) -> None: ...

    def load(self) -> OAuth2Token | None: ...


class FileTokenStorage:
    def __init__(self, path: str | Path):
        self.path: Path = Path(os.path.expanduser(str(path)))

    def save(self, token: OAuth2Token) -> None:
        os.makedirs(self.path, exist_ok=True)
        with open(self.path / OAUTH2_TOKEN_FILE, "w") as f:
            payload = cast(dict[str, object], asdict(token))
            json.dump(payload, f, indent=4)

    def load(self) -> OAuth2Token | None:
        oauth2_path = self.path / OAUTH2_TOKEN_FILE
        if not oauth2_path.exists():
            return None

        with open(oauth2_path) as f:
            data = cast(_TokenData, cast(object, json.load(f)))
            return _build_token(data)


class EnvTokenStorage:
    def save(self, token: OAuth2Token) -> None:
        """No-op: env vars are read-only at runtime, so refreshed tokens
        are not persisted.

        This is intentional for CI and container use cases where GARTH_TOKEN
        provides the initial auth state.
        """
        _ = token
        return None

    def load(self) -> OAuth2Token | None:
        token = os.getenv("GARTH_TOKEN")
        if not token:
            return None

        data = cast(object, json.loads(base64.b64decode(token)))
        if (
            isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], dict)
        ):
            return _build_token(cast(_TokenData, cast(object, data[0])))

        return None


def _build_token(data: _TokenData) -> OAuth2Token:
    return OAuth2Token(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_in=data.get("expires_in"),
        token_type=data.get("token_type", "Bearer"),
        expires_at=data.get("expires_at"),
        refresh_token_expires_in=data.get("refresh_token_expires_in"),
        refresh_token_expires_at=data.get("refresh_token_expires_at"),
        scope=data.get("scope"),
        jti=data.get("jti"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        client_id=data.get("client_id"),
    )


__all__ = ["TokenStorage", "FileTokenStorage", "EnvTokenStorage"]
