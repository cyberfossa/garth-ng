# ruff: noqa: E402, I001
from __future__ import annotations

import typer


data_app = typer.Typer(help="Garmin Connect data commands.")


@data_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


from garth.cli.data.activity import app as activity_app
from garth.cli.data.body_battery import app as body_battery_app
from garth.cli.data.body_battery_stress import app as body_battery_stress_app
from garth.cli.data.daily_summary import app as daily_summary_app
from garth.cli.data.fitness_activity import app as fitness_activity_app
from garth.cli.data.garmin_scores import app as garmin_scores_app
from garth.cli.data.heart_rate import app as heart_rate_app
from garth.cli.data.hrv import app as hrv_app
from garth.cli.data.morning_readiness import app as morning_readiness_app
from garth.cli.data.sleep import app as sleep_app
from garth.cli.data.sleep_detail import app as sleep_detail_app
from garth.cli.data.training_readiness import app as training_readiness_app
from garth.cli.data.weight import app as weight_app
from garth.cli.data.blood_pressure import app as blood_pressure_app
from garth.cli.data.nutrition import app as nutrition_app
from garth.cli.data.personal_record import app as personal_record_app
from garth.cli.data.personal_record_type import app as personal_record_type_app
from garth.cli.data.weight_goal import app as weight_goal_app
from garth.cli.data.steps_goal import app as steps_goal_app


data_app.add_typer(body_battery_app, name="body-battery")
data_app.add_typer(body_battery_stress_app, name="body-battery-stress")
data_app.add_typer(heart_rate_app, name="heart-rate")
data_app.add_typer(sleep_app, name="sleep")
data_app.add_typer(sleep_detail_app, name="sleep-detail")
data_app.add_typer(daily_summary_app, name="daily-summary")
data_app.add_typer(garmin_scores_app, name="garmin-scores")
data_app.add_typer(hrv_app, name="hrv")
data_app.add_typer(morning_readiness_app, name="morning-readiness")
data_app.add_typer(training_readiness_app, name="training-readiness")
data_app.add_typer(weight_app, name="weight")
data_app.add_typer(activity_app, name="activity")
data_app.add_typer(fitness_activity_app, name="fitness-activity")
data_app.add_typer(blood_pressure_app, name="blood-pressure")
data_app.add_typer(nutrition_app, name="nutrition")
data_app.add_typer(personal_record_app, name="personal-record")
data_app.add_typer(personal_record_type_app, name="personal-record-type")
data_app.add_typer(weight_goal_app, name="weight-goal")
data_app.add_typer(steps_goal_app, name="steps-goal")
