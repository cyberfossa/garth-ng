from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import _dump_item, _resume
from garth.data import PersonalRecord


app = typer.Typer(help="Personal record data.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command(name="list")
def list_(
    ctx: typer.Context,
    activity_id: Annotated[
        int | None,
        typer.Option("--activity-id", help="Filter by activity ID."),
    ] = None,
) -> None:
    """List personal records, optionally filtered by activity."""
    _resume(ctx)
    if activity_id is not None:
        _dump_item(PersonalRecord.for_activity(activity_id))
    else:
        _dump_item(PersonalRecord.list())
