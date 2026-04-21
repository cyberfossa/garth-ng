from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import _dump_item, _resume
from garth.data import NutritionLog, NutritionSettings, NutritionStatus


app = typer.Typer(help="Nutrition data.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


log_app = typer.Typer(help="Nutrition food log.")


@log_app.callback(invoke_without_command=True)
def log_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@log_app.command(name="get")
def log_get(
    ctx: typer.Context,
    day: Annotated[
        str | None,
        typer.Option("--day", help="Date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    """Get nutrition food log for a given day."""
    _resume(ctx)
    _dump_item(NutritionLog.get(day))


settings_app = typer.Typer(help="Nutrition settings.")


@settings_app.callback(invoke_without_command=True)
def settings_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@settings_app.command(name="get")
def settings_get(
    ctx: typer.Context,
    day: Annotated[
        str | None,
        typer.Option("--day", help="Date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    """Get nutrition settings for a given day."""
    _resume(ctx)
    _dump_item(NutritionSettings.get(day))


status_app = typer.Typer(help="Nutrition status.")


@status_app.callback(invoke_without_command=True)
def status_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@status_app.command(name="get")
def status_get(
    ctx: typer.Context,
) -> None:
    """Get current nutrition status."""
    _resume(ctx)
    _dump_item(NutritionStatus.get())


app.add_typer(log_app, name="log")
app.add_typer(settings_app, name="settings")
app.add_typer(status_app, name="status")
