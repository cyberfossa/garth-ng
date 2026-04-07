from datetime import date, timedelta

from garth import DailyStress, WeeklyStress
from garth.http import Client


def test_daily_stress(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/stats/cassettes/test_daily_stress.yaml",
    )
    end = date(2023, 7, 20)
    days = 20
    daily_stress = DailyStress.list(end, days, client=authed_client)
    assert daily_stress[-1].calendar_date == end
    assert len(daily_stress) == days


def test_daily_stress_pagination(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/stats/cassettes/test_daily_stress_pagination.yaml",
    )
    end = date(2023, 7, 20)
    days = 60
    daily_stress = DailyStress.list(end, days, client=authed_client)
    assert len(daily_stress) == days


def test_weekly_stress(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/stats/cassettes/test_weekly_stress.yaml",
    )
    end = date(2023, 7, 20)
    weeks = 52
    weekly_stress = WeeklyStress.list(end, weeks, client=authed_client)
    assert len(weekly_stress) == weeks
    assert weekly_stress[-1].calendar_date == end - timedelta(days=6)


def test_weekly_stress_pagination(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/stats/cassettes/test_weekly_stress_pagination.yaml",
    )
    end = date(2023, 7, 20)
    weeks = 60
    weekly_stress = WeeklyStress.list(end, weeks, client=authed_client)
    assert len(weekly_stress) == weeks
    assert weekly_stress[-1].calendar_date == end - timedelta(days=6)


def test_weekly_stress_beyond_data(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/stats/cassettes/test_weekly_stress_beyond_data.yaml",
    )
    end = date(2023, 7, 20)
    weeks = 1000
    weekly_stress = WeeklyStress.list(end, weeks, client=authed_client)
    assert len(weekly_stress) < weeks
