from unittest.mock import MagicMock

from garth import NutritionLog, NutritionSettings, NutritionStatus
from garth.http import Client
from tests.fixture_helpers import load_fixture


def test_nutrition_log_get(authed_client: Client):
    fixture = load_fixture("nutrition_food_logs.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = NutritionLog.get("2026-04-06", client=authed_client)
    assert result is not None
    assert result.meal_date is not None


def test_nutrition_log_get_none(authed_client: Client):
    authed_client.connectapi = MagicMock(return_value=None)
    result = NutritionLog.get("2026-04-06", client=authed_client)
    assert result is None


def test_nutrition_settings_get(authed_client: Client):
    authed_client.connectapi = MagicMock(return_value=None)
    result = NutritionSettings.get("2026-04-06", client=authed_client)
    assert result is None


def test_nutrition_status_get(authed_client: Client):
    fixture = load_fixture("nutrition_current_status.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = NutritionStatus.get(client=authed_client)
    assert result is not None
    assert result.current_status == "NUTRITION_NONE"
    assert result.has_used_nutrition is False
    assert result.has_used_mfp is False


def test_nutrition_status_get_none(authed_client: Client):
    authed_client.connectapi = MagicMock(return_value=None)
    result = NutritionStatus.get(client=authed_client)
    assert result is None
