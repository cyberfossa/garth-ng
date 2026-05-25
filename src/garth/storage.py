from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Protocol, cast

from .auth_tokens import OAuth2Token
from .utils import asdict


OAUTH2_TOKEN_FILE = "oauth2_token.json"


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
            return OAuth2Token(**json.load(f))


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

        data = json.loads(base64.b64decode(token))
        if (
            isinstance(data, list)
            and len(data) == 1
            and isinstance(data[0], dict)
        ):
            return OAuth2Token(**data[0])

        return None


__all__ = ["TokenStorage", "FileTokenStorage", "EnvTokenStorage"]
