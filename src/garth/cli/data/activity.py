from __future__ import annotations

from typing import Annotated

import typer

from garth.cli._helpers import _dump_item, _dump_json, _dump_list, _resume
from garth.data import Activity


app = typer.Typer(help="Activity data.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command(name="list")
def list_(
    ctx: typer.Context,
    limit: Annotated[
        int,
        typer.Option("--limit", min=1, help="Maximum activities."),
    ] = 20,
    start: Annotated[
        int,
        typer.Option("--start", min=0, help="Start offset."),
    ] = 0,
) -> None:
    _resume(ctx)
    _dump_list(Activity.list(limit=limit, start=start))


@app.command(name="get")
def get(
    ctx: typer.Context,
    activity_id: Annotated[
        int,
        typer.Argument(help="Activity ID."),
    ],
) -> None:
    _resume(ctx)
    _dump_item(Activity.get(activity_id))


@app.command(name="update")
def update(
    ctx: typer.Context,
    activity_id: Annotated[
        int,
        typer.Argument(help="Activity ID."),
    ],
    name: Annotated[
        str | None,
        typer.Option("--name", help="New activity name."),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option(
            "--description",
            help="New activity description.",
        ),
    ] = None,
) -> None:
    if name is None and description is None:
        typer.echo("Provide --name or --description.", err=True)
        raise typer.Exit(code=1)
    _resume(ctx)
    Activity.update(
        activity_id,
        name=name,
        description=description,
    )
    _dump_json({"updated": activity_id})
