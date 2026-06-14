from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import _dump_item, _resume
from garth.data import WeightGoal


app = typer.Typer(help="Weight goal data.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command(name="get")
def get(
    ctx: typer.Context,
    day: Annotated[
        str | None,
        typer.Option("--day", help="Date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    """Get weight goal for a given day."""
    _resume(ctx)
    _dump_item(WeightGoal.get(day))
