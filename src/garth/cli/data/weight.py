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


@app.command(name="delete")
def delete(
    ctx: typer.Context,
    sample_pk: Annotated[
        int, typer.Argument(help="Unique identifier of the weight record.")
    ],
    day: Annotated[
        str | None,
        typer.Option("--day", help="Date (YYYY-MM-DD). Defaults to today."),
    ] = None,
) -> None:
    """Delete a weight record."""
    _resume(ctx)
    WeightData.delete(sample_pk=sample_pk, day=day)
    _dump_json({"deleted": sample_pk})


@app.command(name="create-body-composition")
def create_body_composition(
    ctx: typer.Context,
    weight: Annotated[
        float, typer.Argument(help="Weight in kilograms (e.g. 72.5).")
    ],
    percent_fat: Annotated[
        float | None,
        typer.Option("--percent-fat", help="Body fat percentage."),
    ] = None,
    percent_hydration: Annotated[
        float | None,
        typer.Option("--percent-hydration", help="Body hydration percentage."),
    ] = None,
    muscle_mass: Annotated[
        float | None,
        typer.Option("--muscle-mass", help="Muscle mass in kilograms."),
    ] = None,
    bone_mass: Annotated[
        float | None,
        typer.Option("--bone-mass", help="Bone mass in kilograms."),
    ] = None,
    bmi: Annotated[
        float | None, typer.Option("--bmi", help="Body mass index.")
    ] = None,
    basal_met: Annotated[
        float | None,
        typer.Option("--basal-met", help="Basal metabolic rate in kcal/day."),
    ] = None,
    active_met: Annotated[
        float | None,
        typer.Option(
            "--active-met", help="Active metabolic rate in kcal/day."
        ),
    ] = None,
    metabolic_age: Annotated[
        int | None,
        typer.Option("--metabolic-age", help="Metabolic age in years."),
    ] = None,
    physique_rating: Annotated[
        int | None,
        typer.Option(
            "--physique-rating",
            min=0,
            max=254,
            help="Physique rating (0-254).",
        ),
    ] = None,
    visceral_fat_mass: Annotated[
        float | None,
        typer.Option(
            "--visceral-fat-mass", help="Visceral fat mass in kilograms."
        ),
    ] = None,
    visceral_fat_rating: Annotated[
        int | None,
        typer.Option(
            "--visceral-fat-rating",
            min=0,
            max=254,
            help="Visceral fat rating (0-254).",
        ),
    ] = None,
    timestamp: Annotated[
        str | None,
        typer.Option(
            "--timestamp", help="ISO 8601 timestamp. Defaults to now."
        ),
    ] = None,
) -> None:
    """Create a body composition entry."""
    _resume(ctx)
    ts = None
    if timestamp:
        try:
            ts = datetime.fromisoformat(timestamp)
        except ValueError:
            raise typer.BadParameter(f"Invalid timestamp: {timestamp}")
    WeightData.create_body_composition(
        weight=weight,
        percent_fat=percent_fat,
        percent_hydration=percent_hydration,
        muscle_mass=muscle_mass,
        bone_mass=bone_mass,
        bmi=bmi,
        basal_met=basal_met,
        active_met=active_met,
        metabolic_age=metabolic_age,
        physique_rating=physique_rating,
        visceral_fat_mass=visceral_fat_mass,
        visceral_fat_rating=visceral_fat_rating,
        timestamp=ts,
    )
    _dump_json({"uploaded": True})
