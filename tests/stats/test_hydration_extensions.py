from unittest.mock import patch

from garth import DailyHydration
from garth.http import Client
from tests.fixture_helpers import load_fixture


def test_weekly_empty_response(authed_client: Client):
    """Test weekly() with empty list response."""
    fixture = load_fixture("hydration_weekly.json", subdir="stats")
    with patch.object(authed_client, "connectapi", return_value=fixture):
        result = DailyHydration.weekly(
            "2026-04-06", weeks=52, client=authed_client
        )
        assert isinstance(result, list)
        assert result == []
        authed_client.connectapi.assert_called_once_with(
            "/usersummary-service/stats/hydration/weekly/2026-04-06/52"
        )


def test_weekly_with_default_date(authed_client: Client):
    """Test weekly() uses today's date when none provided."""
    with patch.object(authed_client, "connectapi", return_value=[]):
        result = DailyHydration.weekly(client=authed_client)
        assert isinstance(result, list)
        call_args = authed_client.connectapi.call_args[0][0]
        assert "/usersummary-service/stats/hydration/weekly/" in call_args
        assert "/52" in call_args


def test_weekly_with_custom_weeks(authed_client: Client):
    """Test weekly() with custom weeks parameter."""
    with patch.object(authed_client, "connectapi", return_value=[]):
        DailyHydration.weekly("2026-01-01", weeks=12, client=authed_client)
        authed_client.connectapi.assert_called_once_with(
            "/usersummary-service/stats/hydration/weekly/2026-01-01/12"
        )


def test_all_data_success(authed_client: Client):
    """Test all_data() returns transformed dict."""
    fixture = load_fixture("hydration_all_data.json", subdir="stats")
    with patch.object(authed_client, "connectapi", return_value=fixture):
        result = DailyHydration.all_data("2026-04-06", client=authed_client)
        assert isinstance(result, dict)
        assert "user_id" in result
        assert "calendar_date" in result
        assert "value_in_ml" in result
        assert "goal_in_ml" in result
        assert "last_entry_timestamp_local" in result
        assert result["user_id"] == 144710582
        assert result["calendar_date"] == "2026-04-06"
        assert result["value_in_ml"] == 2.0
        authed_client.connectapi.assert_called_once_with(
            "/usersummary-service/usersummary/hydration/allData/2026-04-06"
        )


def test_all_data_no_data(authed_client: Client):
    """Test all_data() returns None when no data."""
    with patch.object(authed_client, "connectapi", return_value=None):
        result = DailyHydration.all_data("2026-04-06", client=authed_client)
        assert result is None


def test_all_data_empty_dict(authed_client: Client):
    """Test all_data() with empty dict response returns None."""
    with patch.object(authed_client, "connectapi", return_value={}):
        result = DailyHydration.all_data("2026-04-06", client=authed_client)
        assert result is None


def test_all_data_with_default_date(authed_client: Client):
    """Test all_data() uses today's date when none provided."""
    with patch.object(authed_client, "connectapi", return_value={}):
        DailyHydration.all_data(client=authed_client)
        call_args = authed_client.connectapi.call_args[0][0]
        assert (
            "/usersummary-service/usersummary/hydration/allData/" in call_args
        )
