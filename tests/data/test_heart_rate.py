from garth import DailyHeartRate
from garth.http import Client


def test_daily_heart_rate_get(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_daily_heart_rate_get.yaml",
    )
    hr = DailyHeartRate.get("2026-01-07", client=authed_client)
    assert hr is not None
    assert hr.resting_heart_rate > 0
    assert hr.max_heart_rate >= hr.min_heart_rate
    assert hr.last_seven_days_avg_resting_heart_rate > 0
    assert len(hr.heart_rate_values) > 0


def test_daily_heart_rate_readings(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_daily_heart_rate_readings.yaml",
    )
    hr = DailyHeartRate.get("2026-01-07", client=authed_client)
    assert hr is not None
    readings = hr.readings
    assert len(readings) > 0
    first_reading = readings[0]
    assert first_reading.timestamp is not None
    assert first_reading.heart_rate > 0


def test_daily_heart_rate_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_daily_heart_rate_list.yaml",
    )
    hr_list = DailyHeartRate.list(
        end="2026-01-07", days=3, client=authed_client, max_workers=1
    )
    assert len(hr_list) > 0
    dates = [hr.calendar_date for hr in hr_list]
    assert dates == sorted(dates)
