# ruff: noqa: E402, I001
from __future__ import annotations

import typer

stats_app = typer.Typer(help="Garmin Connect stats commands.")


@stats_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


from garth.cli.stats.steps import app as steps_app
from garth.cli.stats.hydration import app as hydration_app
from garth.cli.stats.stress import app as stress_app
from garth.cli.stats.sleep import app as sleep_app
from garth.cli.stats.hrv import app as hrv_app
from garth.cli.stats.intensity_minutes import app as intensity_minutes_app
from garth.cli.stats.training_status import app as training_status_app

stats_app.add_typer(steps_app, name="steps")
stats_app.add_typer(hydration_app, name="hydration")
stats_app.add_typer(stress_app, name="stress")
stats_app.add_typer(sleep_app, name="sleep")
stats_app.add_typer(hrv_app, name="hrv")
stats_app.add_typer(intensity_minutes_app, name="intensity-minutes")
stats_app.add_typer(training_status_app, name="training-status")
