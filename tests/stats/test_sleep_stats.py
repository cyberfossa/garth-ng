from datetime import date

from garth import DailySleep
from garth.http import Client


def test_daily_sleep(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/stats/cassettes/test_daily_sleep.yaml",
    )
    end = date(2023, 7, 20)
    days = 20
    daily_sleep = DailySleep.list(end, days, client=authed_client)
    assert daily_sleep[-1].calendar_date == end
    assert len(daily_sleep) == days
