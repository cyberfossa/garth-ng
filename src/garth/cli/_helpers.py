from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from typing import cast

import typer

from garth import utils as _utils


asdict = _utils.asdict


def _resume(ctx: typer.Context) -> None:
    """Lifecycle hook placeholder invoked by every CLI command.

    Intentionally a no-op; exists so individual command modules share
    a uniform callback signature that can be extended later without
    touching every call-site.
    """


def _dump_json(data: object) -> None:
    json.dump(data, sys.stdout, indent=2)
    typer.echo()


def _dump_item(item: object) -> None:
    if item is None:
        _dump_json(None)
    elif isinstance(item, list):
        items = cast(list[object], item)
        _dump_json([asdict(i) for i in items])
    else:
        _dump_json(asdict(item))


def _dump_list(items: Sequence[object]) -> None:
    _dump_json([asdict(i) for i in items])
