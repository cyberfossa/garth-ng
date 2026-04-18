from __future__ import annotations

import json
import os
from typing import cast


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "{subdir}", "fixtures")


def load_fixture(
    filename: str, subdir: str = "data"
) -> dict[str, object] | list[object]:
    base = os.path.join(os.path.dirname(__file__), subdir, "fixtures")
    with open(os.path.join(base, filename)) as f:
        payload: object = json.load(f)  # pyright: ignore[reportAny]

    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    if isinstance(payload, list):
        return cast(list[object], payload)
    raise TypeError(f"Fixture {filename!r} is not valid JSON payload")
