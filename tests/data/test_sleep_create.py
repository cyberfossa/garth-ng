from datetime import datetime
from unittest.mock import MagicMock

from garth import SleepData
from garth.data.sleep import DailySleepDTO
from garth.http import Client
from tests.fixture_helpers import load_fixture


def test_sleep_create(authed_client: Client):
    """Test SleepData.create() parsing of fixture data."""
    fixture = load_fixture("sleep_create_response.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    sleep_start = datetime(2026, 4, 6, 22, 0)
    sleep_end = datetime(2026, 4, 7, 6, 0)
    result = SleepData.create(
        sleep_start=sleep_start, sleep_end=sleep_end, client=authed_client
    )
    assert result is not None
    assert isinstance(result, DailySleepDTO)
    assert result.id == -1
    assert result.user_profile_pk == 144710582
    assert result.sleep_time_seconds == 28800
    authed_client.connectapi.assert_called_once()
    call_kwargs = authed_client.connectapi.call_args
    assert call_kwargs.kwargs["method"] == "POST"
    assert call_kwargs.args[0] == "/sleep-service/sleep/dailySleep"


def test_sleep_create_empty_response(authed_client: Client):
    """Test SleepData.create() returns None for 204 response."""
    authed_client.connectapi = MagicMock(return_value=None)
    sleep_start = datetime(2026, 4, 6, 22, 0)
    sleep_end = datetime(2026, 4, 7, 6, 0)
    result = SleepData.create(
        sleep_start=sleep_start, sleep_end=sleep_end, client=authed_client
    )
    assert result is None


def test_sleep_create_timezone_aware(authed_client: Client):
    """Test SleepData.create() with timezone-aware datetimes."""
    from datetime import timedelta, timezone

    fixture = load_fixture("sleep_create_response.json")
    authed_client.connectapi = MagicMock(return_value=fixture)

    tz = timezone(timedelta(hours=2))
    sleep_start = datetime(2026, 4, 6, 22, 0, tzinfo=tz)
    sleep_end = datetime(2026, 4, 7, 6, 0, tzinfo=tz)

    result = SleepData.create(
        sleep_start=sleep_start, sleep_end=sleep_end, client=authed_client
    )

    assert result is not None
    authed_client.connectapi.assert_called_once()
    call_kwargs = authed_client.connectapi.call_args
    posted_json = call_kwargs.kwargs["json"]

    # 22:00 UTC+2 is 20:00 UTC -> 1775505600000 ms
    assert posted_json["sleepStartTimestampGMT"] == 1775505600000
    # 22:00 as local timestamp -> 1775512800000 ms
    assert posted_json["sleepStartTimestampLocal"] == 1775512800000

    # 06:00 UTC+2 is 04:00 UTC -> 1775534400000 ms
    assert posted_json["sleepEndTimestampGMT"] == 1775534400000
    # 06:00 as local timestamp -> 1775541600000 ms
    assert posted_json["sleepEndTimestampLocal"] == 1775541600000
