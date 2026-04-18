from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import _dump_item, _resume
from garth.data import BloodPressure


app = typer.Typer(help="Blood pressure data.")


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
    """Get blood pressure data for a given day."""
    _resume(ctx)
    _dump_item(BloodPressure.get(day))


@app.command(name="create")
def create(
    ctx: typer.Context,
    systolic: Annotated[
        int,
        typer.Option("--systolic", help="Systolic pressure (mmHg)."),
    ],
    diastolic: Annotated[
        int,
        typer.Option("--diastolic", help="Diastolic pressure (mmHg)."),
    ],
    pulse: Annotated[
        int | None,
        typer.Option("--pulse", help="Heart rate (bpm)."),
    ] = None,
    timestamp: Annotated[
        str | None,
        typer.Option("--timestamp", help="ISO 8601 measurement timestamp."),
    ] = None,
) -> None:
    """Create a new blood pressure measurement."""
    _resume(ctx)
    _dump_item(
        BloodPressure.create(
            systolic,
            diastolic,
            pulse=pulse,
            measurement_timestamp_local=timestamp,
        )
    )


@app.command(name="categories")
def categories(
    ctx: typer.Context,
) -> None:
    """List blood pressure measurement categories."""
    _resume(ctx)
    _dump_item(BloodPressure.categories())
