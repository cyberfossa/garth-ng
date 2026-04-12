from __future__ import annotations

import typer

from garth.cli._helpers import _dump_item, _resume
from garth.users import UserProfile, UserSettings


app = typer.Typer(help="Garmin Connect user data.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command()
def profile(ctx: typer.Context) -> None:
    """Get user profile."""
    _resume(ctx)
    _dump_item(UserProfile.get())


@app.command()
def settings(ctx: typer.Context) -> None:
    """Get user settings."""
    _resume(ctx)
    _dump_item(UserSettings.get())
