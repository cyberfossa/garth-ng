from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import (
    _dump_item,  # pyright: ignore[reportPrivateUsage]
    _dump_list,  # pyright: ignore[reportPrivateUsage]
    _resume,  # pyright: ignore[reportPrivateUsage]
)
from garth.stats import DailyHydration


app = typer.Typer(help="Hydration stats.")


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
    _dump_list(DailyHydration.list(end=end, period=days))


@app.command(name="log")
def log(
    ctx: typer.Context,
    value_in_ml: Annotated[
        float,
        typer.Argument(min=0, help="Hydration in milliliters."),
    ],
) -> None:
    _resume(ctx)
    result = DailyHydration.log(value_in_ml)
    _dump_item(result)
