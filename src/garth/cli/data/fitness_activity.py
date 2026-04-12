from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import _dump_list, _resume
from garth.data import FitnessActivity


app = typer.Typer(help="Fitness activity data.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command(name="list")
def list_(
    ctx: typer.Context,
    days: Annotated[
        int,
        typer.Option("--days", min=1, help="Number of days."),
    ] = 7,
    end: Annotated[
        str | None,
        typer.Option("--end", help="End date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    _resume(ctx)
    _dump_list(FitnessActivity.list(end=end, days=days))
