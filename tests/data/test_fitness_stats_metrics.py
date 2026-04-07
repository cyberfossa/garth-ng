from unittest.mock import MagicMock

from garth import FitnessActivity
from garth.http import Client
from tests.fixture_helpers import load_fixture


def test_available_metrics(authed_client: Client) -> None:
    """Test available_metrics returns list of metric names."""
    fixture = load_fixture("fitness_stats_available_metrics.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = FitnessActivity.available_metrics(client=authed_client)
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(metric, str) for metric in result)
    assert "activityType" in result


def test_available_metrics_returns_strings(authed_client: Client) -> None:
    """Test available_metrics returns list of strings only."""
    fixture = load_fixture("fitness_stats_available_metrics.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = FitnessActivity.available_metrics(client=authed_client)
    assert isinstance(result, list)
    for metric in result:
        assert isinstance(metric, str)
        assert len(metric) > 0
