from datetime import date
from unittest.mock import MagicMock

from garth.data.wellness_goals import StepsGoal
from tests.fixture_helpers import load_fixture


class TestStepsGoalGet:
    def test_get_parses_fixture(self, authed_client):
        """Test that StepsGoal.get() parses fixture JSON correctly."""
        fixture = load_fixture("wellness_goals_steps.json")
        authed_client.connectapi = MagicMock(return_value=fixture)

        result = StepsGoal.get("2024-01-15", client=authed_client)

        assert result is not None
        assert isinstance(result, StepsGoal)
        assert result.device_goal == 0
        assert result.user_goal == 0
        assert result.synced_to_device is False
        assert result.effective == "permanently"
        assert result.user_goal_category is None
        assert result.goal_type == "STEPS"

    def test_get_with_none_response(self, authed_client):
        """Test that StepsGoal.get() returns None for empty response."""
        authed_client.connectapi = MagicMock(return_value=None)

        result = StepsGoal.get("2024-01-15", client=authed_client)

        assert result is None

    def test_get_calls_correct_endpoint(self, authed_client):
        """Test that get() calls the correct endpoint."""
        fixture = load_fixture("wellness_goals_steps.json")
        authed_client.connectapi = MagicMock(return_value=fixture)

        StepsGoal.get("2024-01-15", client=authed_client)

        authed_client.connectapi.assert_called_once_with(
            "/wellness-service/wellness/wellness-goals/consolidated/steps/2024-01-15"
        )

    def test_get_with_date_object(self, authed_client):
        """Test that get() handles date objects."""
        fixture = load_fixture("wellness_goals_steps.json")
        authed_client.connectapi = MagicMock(return_value=fixture)

        test_date = date(2024, 1, 15)
        StepsGoal.get(test_date, client=authed_client)

        authed_client.connectapi.assert_called_once_with(
            "/wellness-service/wellness/wellness-goals/consolidated/steps/2024-01-15"
        )

    def test_get_uses_global_client(self, monkeypatch):
        """Test that get() uses global client when not provided."""
        fixture = load_fixture("wellness_goals_steps.json")
        mock_client = MagicMock()
        mock_client.connectapi = MagicMock(return_value=fixture)

        monkeypatch.setattr(
            "garth.data.wellness_goals.http.client", mock_client
        )

        result = StepsGoal.get("2024-01-15")

        assert result is not None
        mock_client.connectapi.assert_called_once()
