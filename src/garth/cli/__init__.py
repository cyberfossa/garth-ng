from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal, cast


try:
    import typer  # pyright: ignore[reportMissingImports]
except ImportError:
    print(
        "Error: `typer` is required for the CLI.\n"
        "Install it using: pip install 'garth-ng[cli]'",
        file=sys.stderr,
    )
    sys.exit(1)

import garth
from garth.cli._helpers import (
    _dump_json,
    _resume,
    asdict,
)
from garth.cli.data import data_app
from garth.cli.stats import stats_app
from garth.cli.users import app as users_app
from garth.exc import GarthException


app = typer.Typer(help="Garmin Connect CLI client.")


def main() -> None:
    app()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    domain: Annotated[
        str,
        typer.Option(
            "-d",
            "--domain",
            help="Garmin Connect domain.",
        ),
    ] = "garmin.com",
    token_dir: Annotated[
        str,
        typer.Option(
            "--token-dir",
            help="Directory with saved tokens.",
        ),
    ] = ".garth",
) -> None:
    garth.configure(domain=domain, garth_home=token_dir)  # pyright: ignore[reportUnknownMemberType]
    try:
        garth.resume()  # pyright: ignore[reportUnknownMemberType]
    except GarthException:
        pass
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


@app.command()
def login(ctx: typer.Context) -> None:
    email = cast(str, typer.prompt("Email"))
    password = cast(str, typer.prompt("Password", hide_input=True))
    _ = garth.login(  # pyright: ignore[reportUnknownMemberType]
        email,
        password,
        prompt_mfa=lambda: cast(str, typer.prompt("MFA code")),
    )
    typer.echo(garth.client.dumps())


@app.command()
def api(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="API path.")],
    method: Annotated[
        Literal["GET", "POST", "PUT", "DELETE"],
        typer.Option(
            "-m",
            "--method",
            help="HTTP method.",
        ),
    ] = "GET",
    data: Annotated[
        str | None,
        typer.Option("--data", help="JSON request body."),
    ] = None,
) -> None:
    """Call Garmin Connect API endpoint."""
    _resume(ctx)
    kwargs: dict[str, object] = {}
    if data:
        try:
            kwargs["json"] = json.loads(data)
        except json.JSONDecodeError as err:
            typer.echo(f"Invalid JSON: {err}", err=True)
            raise typer.Exit(code=1)
    connectapi = cast(Callable[..., object], garth.connectapi)
    result = connectapi(path, method=method, **kwargs)
    _dump_json(result)


@app.command()
def upload(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Argument(
            help="File to upload.",
            exists=True,
        ),
    ],
) -> None:
    """Upload a file to Garmin Connect."""
    _resume(ctx)
    with open(path, "rb") as fp:
        result = garth.upload(fp)
    _dump_json(result)


app.add_typer(data_app, name="data")
app.add_typer(stats_app, name="stats")
app.add_typer(users_app, name="users")


__all__ = ["app", "asdict", "main", "typer"]
