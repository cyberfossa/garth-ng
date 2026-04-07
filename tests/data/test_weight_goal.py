from unittest.mock import MagicMock

from garth import WeightGoal
from garth.http import Client
from tests.fixture_helpers import load_fixture


def test_weight_goal_get(authed_client: Client):
    """Test WeightGoal.get() parsing of fixture data."""
    fixture = load_fixture("weight_goal_get.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = WeightGoal.get("2026-04-06", client=authed_client)
    assert result is not None
    assert result.user_goals == []
    assert result.user_goal_ranges is None
    authed_client.connectapi.assert_called_once_with(
        "/goal-service/goal/user/effective/weightgoal/2026-04-06/2026-04-06"
    )


def test_weight_goal_get_none(authed_client: Client):
    """Test WeightGoal.get() returns None for empty response."""
    authed_client.connectapi = MagicMock(return_value=None)
    result = WeightGoal.get("2026-04-06", client=authed_client)
    assert result is None
