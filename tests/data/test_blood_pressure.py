from unittest.mock import MagicMock

from garth import BloodPressure
from garth.data.blood_pressure import BloodPressureCategory
from garth.http import Client
from tests.fixture_helpers import load_fixture


def test_blood_pressure_get(authed_client: Client):
    """Test BloodPressure.get() parsing of fixture data."""
    fixture = load_fixture("bloodpressure_get.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = BloodPressure.get("2026-04-06", client=authed_client)
    assert result is not None
    assert result.start_date.isoformat() == "2026-04-06"
    assert result.end_date.isoformat() == "2026-04-06"
    assert result.blood_pressure_measurements == []
    authed_client.connectapi.assert_called_once_with(
        "/bloodpressure-service/bloodpressure/dayview/2026-04-06"
    )


def test_blood_pressure_get_none(authed_client: Client):
    """Test BloodPressure.get() returns None for empty response."""
    authed_client.connectapi = MagicMock(return_value=None)
    result = BloodPressure.get("2026-04-06", client=authed_client)
    assert result is None


def test_blood_pressure_create(authed_client: Client):
    """Test BloodPressure.create() posts correct payload."""
    fixture = load_fixture("bloodpressure_get.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = BloodPressure.create(
        systolic=120,
        diastolic=80,
        pulse=72,
        measurement_timestamp_local="2026-04-06T10:30:00",
        client=authed_client,
    )
    assert result is not None
    authed_client.connectapi.assert_called_once_with(
        "/bloodpressure-service/bloodpressure",
        method="POST",
        json={
            "systolic": 120,
            "diastolic": 80,
            "pulse": 72,
            "measurementTimestampLocal": "2026-04-06T10:30:00",
        },
    )


def test_blood_pressure_create_minimal(authed_client: Client):
    """Test BloodPressure.create() with minimal parameters."""
    fixture = load_fixture("bloodpressure_get.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = BloodPressure.create(
        systolic=120,
        diastolic=80,
        client=authed_client,
    )
    assert result is not None
    authed_client.connectapi.assert_called_once_with(
        "/bloodpressure-service/bloodpressure",
        method="POST",
        json={
            "systolic": 120,
            "diastolic": 80,
        },
    )


def test_blood_pressure_create_none(authed_client: Client):
    """Test BloodPressure.create() returns None for 204 response."""
    authed_client.connectapi = MagicMock(return_value=None)
    result = BloodPressure.create(
        systolic=120,
        diastolic=80,
        client=authed_client,
    )
    assert result is None


def test_blood_pressure_categories(authed_client: Client):
    """Test BloodPressure.categories() parses fixture data."""
    fixture = load_fixture("bloodpressure_categories.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    result = BloodPressure.categories(client=authed_client)

    assert len(result) > 0
    assert all(isinstance(cat, BloodPressureCategory) for cat in result)

    # Check that we have categories from both country and default
    categories = [cat.category for cat in result]
    assert "NORMAL" in categories
    authed_client.connectapi.assert_called_once_with(
        "/bloodpressure-service/bloodpressure/category/level"
    )
