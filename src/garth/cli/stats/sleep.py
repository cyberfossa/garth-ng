from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import (  # pyright: ignore[reportPrivateUsage]
    _dump_list,
    _resume,
)
from garth.stats import DailySleep


app = typer.Typer(help="Sleep stats.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command(name="daily")
def daily(
    ctx: typer.Context,
    days: Annotated[
        int, typer.Option("--days", min=1, help="Number of days.")
    ] = 7,
    end: Annotated[
        str | None,
        typer.Option("--end", help="End date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    _resume(ctx)
    _dump_list(DailySleep.list(end=end, period=days))
