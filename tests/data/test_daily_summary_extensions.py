from datetime import date
from unittest.mock import MagicMock

from garth import DailySummary
from garth.http import Client


def test_stats_by_type_with_null_fixture(authed_client: Client) -> None:
    """Test stats_by_type handles null fixture (no data)."""
    authed_client.connectapi = MagicMock(return_value=None)
    result = DailySummary.stats_by_type(
        "2026-01-01", "STEPS", client=authed_client
    )

    assert result is None
    authed_client.connectapi.assert_called_once_with(
        "/usersummary-service/stats/daily/2026-01-01/2026-01-01",
        params={"statsType": "STEPS"},
    )


def test_stats_by_type_with_data(authed_client: Client) -> None:
    """Test stats_by_type returns dict when data present."""
    fixture: dict = {"value": 10000, "unitKey": "STEPS"}
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = DailySummary.stats_by_type(
        "2026-01-01", "STEPS", client=authed_client
    )

    assert result is not None
    assert isinstance(result, dict)
    authed_client.connectapi.assert_called_once_with(
        "/usersummary-service/stats/daily/2026-01-01/2026-01-01",
        params={"statsType": "STEPS"},
    )


def test_stats_by_type_empty(authed_client: Client) -> None:
    """Test stats_by_type returns None for empty response."""
    authed_client.connectapi = MagicMock(return_value=None)
    result = DailySummary.stats_by_type(
        "2026-01-01", "CALORIES", client=authed_client
    )

    assert result is None
    authed_client.connectapi.assert_called_once_with(
        "/usersummary-service/stats/daily/2026-01-01/2026-01-01",
        params={"statsType": "CALORIES"},
    )


def test_stats_by_type_default_stats_type(authed_client: Client) -> None:
    """Test stats_by_type defaults to STEPS when no stats_type specified."""
    fixture: dict = {"value": 10000}
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = DailySummary.stats_by_type("2026-01-01", client=authed_client)

    assert result is not None
    authed_client.connectapi.assert_called_once_with(
        "/usersummary-service/stats/daily/2026-01-01/2026-01-01",
        params={"statsType": "STEPS"},
    )


def test_stats_by_type_uses_default_client(authed_client: Client) -> None:
    """Test stats_by_type uses default client when none provided."""
    import garth.http as http_module

    original_client = http_module.client
    try:
        http_module.client = authed_client
        authed_client.connectapi = MagicMock(return_value={"value": 5000})

        result = DailySummary.stats_by_type("2026-01-01")

        assert result is not None
        authed_client.connectapi.assert_called()
    finally:
        http_module.client = original_client


def test_wellness_chart_with_empty_list(authed_client: Client) -> None:
    """Test wellness_chart returns empty list when fixture is empty list."""
    authed_client.connectapi = MagicMock(return_value=[])
    result = DailySummary.wellness_chart("2026-01-01", client=authed_client)

    assert result == []
    authed_client.connectapi.assert_called_once_with(
        "/wellness-service/wellness/dailySummaryChart",
        params={"date": "2026-01-01"},
    )


def test_wellness_chart_with_data(authed_client: Client) -> None:
    """Test wellness_chart returns list when data present."""
    fixture = [{"time": 1234567890, "value": 85}]
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = DailySummary.wellness_chart("2026-01-01", client=authed_client)

    assert result == fixture
    authed_client.connectapi.assert_called_once_with(
        "/wellness-service/wellness/dailySummaryChart",
        params={"date": "2026-01-01"},
    )


def test_wellness_chart_empty(authed_client: Client) -> None:
    """Test wellness_chart returns None for None response."""
    authed_client.connectapi = MagicMock(return_value=None)
    result = DailySummary.wellness_chart("2026-01-01", client=authed_client)

    assert result is None
    authed_client.connectapi.assert_called_once_with(
        "/wellness-service/wellness/dailySummaryChart",
        params={"date": "2026-01-01"},
    )


def test_wellness_chart_uses_default_client(authed_client: Client) -> None:
    """Test wellness_chart uses default client when none provided."""
    import garth.http as http_module

    original_client = http_module.client
    try:
        http_module.client = authed_client
        authed_client.connectapi = MagicMock(return_value=[])

        result = DailySummary.wellness_chart("2026-01-01")

        assert result == []
        authed_client.connectapi.assert_called()
    finally:
        http_module.client = original_client
