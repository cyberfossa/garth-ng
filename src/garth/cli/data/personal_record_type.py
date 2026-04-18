from __future__ import annotations

import typer

from garth.cli._helpers import _dump_item, _resume
from garth.data import PersonalRecordType


app = typer.Typer(help="Personal record type data.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command(name="list")
def list_(
    ctx: typer.Context,
) -> None:
    """List all personal record types."""
    _resume(ctx)
    _dump_item(PersonalRecordType.list())
