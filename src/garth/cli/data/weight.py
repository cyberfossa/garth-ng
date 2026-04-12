from __future__ import annotations

from datetime import datetime
from typing import Annotated

import typer

from garth.cli._helpers import _dump_item, _dump_json, _dump_list, _resume
from garth.data import WeightData


app = typer.Typer(help="Weight data.")


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
    ] = 1,
    end: Annotated[
        str | None,
        typer.Option("--end", help="End date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    """List weight data."""
    _resume(ctx)
    _dump_list(WeightData.list(end=end, days=days))


@app.command(name="get")
def get(
    ctx: typer.Context,
    day: Annotated[
        str | None,
        typer.Option("--day", help="Date (YYYY-MM-DD). Defaults to today."),
    ] = None,
) -> None:
    """Get weight data for a single day."""
    _resume(ctx)
    _dump_item(WeightData.get(day=day))


@app.command(name="create")
def create(
    ctx: typer.Context,
    weight: Annotated[
        float, typer.Argument(help="Weight in kilograms (e.g. 72.5).")
    ],
    timestamp: Annotated[
        str | None,
        typer.Option(
            "--timestamp",
            help="ISO 8601 timestamp (e.g. 2024-01-15T08:30:00). Defaults to "
            "now.",
        ),
    ] = None,
) -> None:
    """Create a weight entry."""
    _resume(ctx)
    ts = None
    if timestamp:
        try:
            ts = datetime.fromisoformat(timestamp)
        except ValueError:
            raise typer.BadParameter(f"Invalid timestamp: {timestamp}")
    WeightData.create(weight=weight, timestamp=ts)
    _dump_json({"created": weight})
