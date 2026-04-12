from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import _dump_item, _dump_list, _resume
from garth.data import GarminScoresData


app = typer.Typer(help="Garmin scores data.")


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
    _resume(ctx)
    _dump_item(GarminScoresData.get(day))


@app.command(name="list")
def list_(
    ctx: typer.Context,
    days: Annotated[
        int,
        typer.Option("--days", min=1, help="Number of days."),
    ] = 7,
    end: Annotated[
        str | None,
        typer.Option("--end", help="End date."),
    ] = None,
) -> None:
    _resume(ctx)
    _dump_list(GarminScoresData.list(end=end, days=days))
