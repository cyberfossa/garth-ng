from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, cast

import typer

from garth.cli._helpers import _dump_item, _dump_list, _resume
from garth.data import HRVData


app = typer.Typer(help="HRV data.")


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
    _dump_item(HRVData.get(day))


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
    list_fn = cast(Callable[..., Sequence[object]], HRVData.list)
    _dump_list(list_fn(end=end, days=days))
