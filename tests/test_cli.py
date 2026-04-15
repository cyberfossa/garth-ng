import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import cast
from unittest.mock import patch

from typer import Typer

import garth.cli as cli_mod


def _runner():
    from typer.testing import CliRunner

    return CliRunner()


def _app() -> Typer:
    return cli_mod.app


def test_help():
    runner = _runner()
    result = runner.invoke(_app(), ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_no_args_shows_help():
    runner = _runner()
    result = runner.invoke(_app(), [])
    assert result.exit_code == 0
    assert "garmin" in result.output.lower()


def test_login():
    runner = _runner()
    captured: dict[str, object] = {}

    def _fake_login(
        email: str,
        password: str,
        prompt_mfa: Callable[..., object],
    ) -> object:
        captured["email"] = email
        captured["password"] = password
        captured["prompt_mfa"] = prompt_mfa
        return None

    with (
        patch("garth.login", side_effect=_fake_login) as mock_login,
        patch("garth.client.dumps", return_value="token_data") as mock_dumps,
    ):
        result = runner.invoke(
            _app(),
            ["login"],
            input="test@example.com\nsecret\n",
        )

    assert result.exit_code == 0
    assert "token_data" in result.output
    mock_login.assert_called_once()
    mock_dumps.assert_called_once()
    assert captured["email"] == "test@example.com"
    assert captured["password"] == "secret"
    assert callable(captured["prompt_mfa"])


def test_api_get():
    runner = _runner()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.connectapi",
            return_value={"userName": "testuser"},
        ) as mock_api,
    ):
        result = runner.invoke(
            _app(),
            ["api", "/userprofile-service/socialProfile"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output) == {"userName": "testuser"}
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_api.assert_called_once_with(
        "/userprofile-service/socialProfile",
        method="GET",
    )


def test_api_post_with_data():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch(
            "garth.connectapi",
            return_value=[{"activityId": 1}],
        ) as mock_api,
    ):
        result = runner.invoke(
            _app(),
            [
                "api",
                "/activitylist-service/activities",
                "--method",
                "POST",
                "--data",
                '{"limit": 10}',
            ],
        )
    assert result.exit_code == 0
    mock_api.assert_called_once_with(
        "/activitylist-service/activities",
        method="POST",
        json={"limit": 10},
    )


def test_api_custom_token_dir(tmp_path):
    runner = _runner()
    token_dir = str(tmp_path / "tokens")
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.connectapi", return_value={}),
    ):
        result = runner.invoke(
            _app(),
            ["--token-dir", token_dir, "api", "/some/path"],
        )
    assert result.exit_code == 0
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=token_dir
    )
    mock_resume.assert_called_once_with()


def test_steps():
    runner = _runner()
    from datetime import date

    from garth.stats import DailySteps

    fake_steps = [
        DailySteps(
            calendar_date=date(2024, 6, d),
            total_steps=8000 + d * 100,
            total_distance=5000 + d * 50,
            step_goal=10000,
        )
        for d in (13, 14, 15)
    ]
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.stats.DailySteps.list",
            return_value=fake_steps,
        ) as mock_list,
    ):
        result = runner.invoke(
            _app(),
            [
                "stats",
                "steps",
                "daily",
                "--days",
                "3",
                "--end",
                "2024-06-15",
            ],
        )
    assert result.exit_code == 0
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end="2024-06-15", period=3)
    data = cast(list[dict[str, object]], json.loads(result.output))
    assert len(data) == 3
    assert data[0]["calendar_date"] == "2024-06-13"
    assert data[0]["total_steps"] == 9300


def test_main_help_contains_groups():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "stats" in result.output
    assert "data" in result.output
    assert "users" in result.output
    assert "upload" in result.output


def test_steps_command_removed():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["steps"])
    assert result.exit_code != 0


def test_stats_daily_steps():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.DailySteps.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "steps", "daily"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_daily_hydration():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.DailyHydration.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(
            app, ["stats", "hydration", "daily", "--days", "2"]
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=2)


def test_stats_daily_stress():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.DailyStress.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "stress", "daily"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_daily_sleep():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.DailySleep.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(
            app, ["stats", "sleep", "daily", "--end", "2024-01-15"]
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end="2024-01-15", period=7)


def test_stats_daily_hrv_default_28_days():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.DailyHRV.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "hrv", "daily"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=28)


def test_stats_daily_intensity_minutes():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.stats.DailyIntensityMinutes.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "intensity-minutes", "daily"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_daily_training_status():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.stats.DailyTrainingStatus.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "training-status", "daily"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_weekly_steps():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.WeeklySteps.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "steps", "weekly"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_weekly_stress():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.WeeklyStress.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "stress", "weekly"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_weekly_intensity_minutes():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.stats.WeeklyIntensityMinutes.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "intensity-minutes", "weekly"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_weekly_training_status():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.stats.WeeklyTrainingStatus.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "training-status", "weekly"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_monthly_training_status():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.stats.MonthlyTrainingStatus.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(app, ["stats", "training-status", "monthly"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, period=7)


def test_stats_hydration_log():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.stats.DailyHydration.log", return_value=None) as mock_log,
    ):
        result = runner.invoke(app, ["stats", "hydration", "log", "500"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_log.assert_called_once_with(500.0)


def test_stats_help_lists_all_subcommands():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["stats", "--help"])
    assert result.exit_code == 0
    commands = [
        "steps",
        "hydration",
        "stress",
        "sleep",
        "hrv",
        "intensity-minutes",
        "training-status",
    ]
    for command in commands:
        assert command in result.output


def test_stats_steps_help():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["stats", "steps", "--help"])
    assert result.exit_code == 0
    assert "daily" in result.output
    assert "weekly" in result.output


def test_stats_help_lists_concept_groups():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["stats", "--help"])
    assert result.exit_code == 0
    assert "steps" in result.output
    assert "hydration" in result.output
    assert "stress" in result.output
    assert "sleep" in result.output
    assert "hrv" in result.output
    assert "intensity-minutes" in result.output
    assert "training-status" in result.output


def test_data_body_battery_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.BodyBatteryData.get", return_value=[]) as mock_get,
    ):
        result = runner.invoke(app, ["data", "body-battery", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_body_battery_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.BodyBatteryData.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(
            app,
            ["data", "body-battery", "list", "--days", "2"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=2)


def test_data_body_battery_returns_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch(
            "garth.data.BodyBatteryData.get",
            return_value=[],
        ),
    ):
        result = runner.invoke(app, ["data", "body-battery", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []


def test_data_body_battery_stress_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.DailyBodyBatteryStress.get",
            return_value=None,
        ) as mock_get,
    ):
        result = runner.invoke(
            app,
            ["data", "body-battery-stress", "get"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_body_battery_stress_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.DailyBodyBatteryStress.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(
            app,
            ["data", "body-battery-stress", "list", "--days", "3"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=3)


def test_data_heart_rate_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.DailyHeartRate.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["data", "heart-rate", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_heart_rate_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.DailyHeartRate.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(
            app, ["data", "heart-rate", "list", "--days", "5"]
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=5)


def test_data_sleep_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.DailySleepData.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["data", "sleep", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_sleep_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.DailySleepData.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["data", "sleep", "list", "--days", "2"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=2)


def test_data_daily_summary_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.DailySummary.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["data", "daily-summary", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_daily_summary_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.DailySummary.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(
            app,
            ["data", "daily-summary", "list", "--days", "9"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=9)


def test_data_garmin_scores_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.GarminScoresData.get", return_value=None
        ) as mock_get,
    ):
        result = runner.invoke(app, ["data", "garmin-scores", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_garmin_scores_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.GarminScoresData.list", return_value=[]
        ) as mock_list,
    ):
        result = runner.invoke(
            app,
            ["data", "garmin-scores", "list", "--days", "4"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=4)


def test_data_hrv_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.HRVData.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["data", "hrv", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_hrv_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.HRVData.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["data", "hrv", "list", "--days", "7"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=7)


def test_data_morning_readiness_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.MorningTrainingReadinessData.get",
            return_value=None,
        ) as mock_get,
    ):
        result = runner.invoke(app, ["data", "morning-readiness", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_morning_readiness_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.MorningTrainingReadinessData.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(
            app,
            ["data", "morning-readiness", "list", "--days", "6"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=6)


def test_data_training_readiness_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.TrainingReadinessData.get",
            return_value=None,
        ) as mock_get,
    ):
        result = runner.invoke(app, ["data", "training-readiness", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None)


def test_data_training_readiness_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch(
            "garth.data.TrainingReadinessData.list",
            return_value=[],
        ) as mock_list,
    ):
        result = runner.invoke(
            app,
            ["data", "training-readiness", "list", "--days", "8"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=8)


def test_data_sleep_detail_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.SleepData.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["data", "sleep-detail", "get"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None, buffer_minutes=60)


def test_data_sleep_detail_buffer_minutes():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.SleepData.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(
            app,
            ["data", "sleep-detail", "get", "--buffer-minutes", "30"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(None, buffer_minutes=30)


def test_data_sleep_detail_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.SleepData.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(
            app, ["data", "sleep-detail", "list", "--days", "2"]
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=2)


def test_data_activity_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.Activity.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["data", "activity", "list"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(limit=20, start=0)


def test_data_activity_get():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.Activity.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["data", "activity", "get", "123"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once_with(123)


def test_data_activity_update():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.Activity.update", return_value=None) as mock_update,
    ):
        result = runner.invoke(
            app,
            ["data", "activity", "update", "123", "--name", "Run"],
        )
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == {"updated": 123}
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_update.assert_called_once_with(123, name="Run", description=None)


def test_data_activity_update_requires_field():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["data", "activity", "update", "123"])
    assert result.exit_code != 0


def test_data_fitness_activity_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.FitnessActivity.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["data", "fitness-activity", "list"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=7)


def test_data_weight_list():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.data.WeightData.list", return_value=[]) as mock_list,
    ):
        result = runner.invoke(app, ["data", "weight", "list", "--days", "3"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == []
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_list.assert_called_once_with(end=None, days=3)


def test_data_help_lists_all_subcommands():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["data", "--help"])
    assert result.exit_code == 0
    commands = [
        "body-battery",
        "body-battery-stress",
        "heart-rate",
        "sleep",
        "daily-summary",
        "garmin-scores",
        "hrv",
        "morning-readiness",
        "training-readiness",
        "sleep-detail",
        "activity",
        "fitness-activity",
        "weight",
    ]
    for command in commands:
        assert command in result.output


def test_data_body_battery_help():
    runner = _runner()
    app = _app()
    result = runner.invoke(app, ["data", "body-battery", "--help"])
    assert result.exit_code == 0
    assert "get" in result.output
    assert "list" in result.output


def test_users_profile():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.users.UserProfile.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["users", "profile"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once()


def test_users_settings():
    runner = _runner()
    app = _app()
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.users.UserSettings.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(app, ["users", "settings"])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) is None
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_get.assert_called_once()


def test_upload(tmp_path: Path):
    runner = _runner()
    app = _app()
    tmp_file = tmp_path / "sample.fit"
    _ = tmp_file.write_bytes(b"fit-data")
    with (
        patch("garth.configure") as mock_configure,
        patch("garth.resume") as mock_resume,
        patch("garth.upload", return_value={"status": "ok"}) as mock_upload,
    ):
        result = runner.invoke(app, ["upload", str(tmp_file)])
    assert result.exit_code == 0
    assert json.loads(result.output.strip()) == {"status": "ok"}
    mock_configure.assert_called_once_with(
        domain="garmin.com", garth_home=".garth"
    )
    mock_resume.assert_called_once_with()
    mock_upload.assert_called_once()


def test_api_invalid_json():
    runner = _runner()
    with patch("garth.configure"), patch("garth.resume"):
        result = runner.invoke(_app(), ["api", "/test", "--data", "not-json"])
    assert result.exit_code == 1
    assert "Invalid JSON" in result.output


def test_data_body_battery_list_negative_days():
    runner = _runner()
    with patch("garth.configure"), patch("garth.resume"):
        result = runner.invoke(
            _app(), ["data", "body-battery", "list", "--days", "0"]
        )
    assert result.exit_code == 2


def test_data_daily_summary_list_negative_days():
    runner = _runner()
    with patch("garth.configure"), patch("garth.resume"):
        result = runner.invoke(
            _app(), ["data", "daily-summary", "list", "--days", "-1"]
        )
    assert result.exit_code == 2


def test_data_activity_update_requires_field_message():
    runner = _runner()
    result = runner.invoke(_app(), ["data", "activity", "update", "123"])
    assert result.exit_code == 1
    assert "Provide" in result.output


def test_data_weight_get():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(_app(), ["data", "weight", "get"])
    assert result.exit_code == 0
    assert "null" in result.output
    mock_get.assert_called_once_with(day=None)


def test_data_weight_get_with_day():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.get", return_value=None) as mock_get,
    ):
        result = runner.invoke(
            _app(), ["data", "weight", "get", "--day", "2024-01-15"]
        )
    assert result.exit_code == 0
    mock_get.assert_called_once_with(day="2024-01-15")


def test_data_weight_create():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.create") as mock_create,
    ):
        result = runner.invoke(_app(), ["data", "weight", "create", "72.5"])
    assert result.exit_code == 0
    assert '"created": 72.5' in result.output
    mock_create.assert_called_once_with(weight=72.5, timestamp=None)


def test_data_weight_create_with_timestamp():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.create") as mock_create,
    ):
        result = runner.invoke(
            _app(),
            [
                "data",
                "weight",
                "create",
                "72.5",
                "--timestamp",
                "2024-01-15T08:30:00",
            ],
        )
    assert result.exit_code == 0
    mock_create.assert_called_once_with(
        weight=72.5, timestamp=datetime.fromisoformat("2024-01-15T08:30:00")
    )


def test_data_weight_create_invalid_timestamp():
    runner = _runner()
    result = runner.invoke(
        _app(),
        ["data", "weight", "create", "72.5", "--timestamp", "not-a-date"],
    )
    assert result.exit_code != 0


def test_data_weight_delete():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.delete") as mock_delete,
    ):
        result = runner.invoke(_app(), ["data", "weight", "delete", "12345"])
    assert result.exit_code == 0
    assert '"deleted": 12345' in result.output
    mock_delete.assert_called_once_with(sample_pk=12345, day=None)


def test_data_weight_delete_with_day():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.delete") as mock_delete,
    ):
        result = runner.invoke(
            _app(),
            ["data", "weight", "delete", "12345", "--day", "2024-01-15"],
        )
    assert result.exit_code == 0
    mock_delete.assert_called_once_with(sample_pk=12345, day="2024-01-15")


def test_data_weight_create_body_composition():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.create_body_composition") as mock_cbc,
    ):
        result = runner.invoke(
            _app(), ["data", "weight", "create-body-composition", "72.5"]
        )
    assert result.exit_code == 0
    assert '"uploaded": true' in result.output
    mock_cbc.assert_called_once_with(
        weight=72.5,
        percent_fat=None,
        percent_hydration=None,
        muscle_mass=None,
        bone_mass=None,
        bmi=None,
        basal_met=None,
        active_met=None,
        metabolic_age=None,
        physique_rating=None,
        visceral_fat_mass=None,
        visceral_fat_rating=None,
        timestamp=None,
    )


def test_data_weight_create_body_composition_with_params():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.create_body_composition") as mock_cbc,
    ):
        result = runner.invoke(
            _app(),
            [
                "data",
                "weight",
                "create-body-composition",
                "72.5",
                "--percent-fat",
                "15.5",
                "--muscle-mass",
                "32.0",
                "--metabolic-age",
                "28",
            ],
        )
    assert result.exit_code == 0
    mock_cbc.assert_called_once_with(
        weight=72.5,
        percent_fat=15.5,
        percent_hydration=None,
        muscle_mass=32.0,
        bone_mass=None,
        bmi=None,
        basal_met=None,
        active_met=None,
        metabolic_age=28,
        physique_rating=None,
        visceral_fat_mass=None,
        visceral_fat_rating=None,
        timestamp=None,
    )


def test_data_weight_create_body_composition_with_timestamp():
    runner = _runner()
    with (
        patch("garth.configure"),
        patch("garth.resume"),
        patch("garth.data.WeightData.create_body_composition") as mock_cbc,
    ):
        result = runner.invoke(
            _app(),
            [
                "data",
                "weight",
                "create-body-composition",
                "72.5",
                "--timestamp",
                "2024-01-15T08:30:00",
            ],
        )
    assert result.exit_code == 0
    mock_cbc.assert_called_once_with(
        weight=72.5,
        percent_fat=None,
        percent_hydration=None,
        muscle_mass=None,
        bone_mass=None,
        bmi=None,
        basal_met=None,
        active_met=None,
        metabolic_age=None,
        physique_rating=None,
        visceral_fat_mass=None,
        visceral_fat_rating=None,
        timestamp=datetime.fromisoformat("2024-01-15T08:30:00"),
    )
