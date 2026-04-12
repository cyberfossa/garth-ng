from datetime import date, datetime, timezone
from unittest.mock import Mock

from garth.data import WeightData
from garth.utils import camel_to_snake_dict
from tests.fixture_helpers import load_fixture


def test_weight_latest_parses_fixture():
    fixture = load_fixture("weight_latest.json")
    weight_data = WeightData(**camel_to_snake_dict(fixture))
    assert weight_data is not None
    assert weight_data.weight == 907.0
    assert weight_data.source_type == "MANUAL"
    assert weight_data.bmi is None
    assert weight_data.body_fat is None


def test_weight_latest_with_mock_client(authed_client):
    fixture = load_fixture("weight_latest.json")
    authed_client.connectapi = Mock(return_value=fixture)

    weight_data = WeightData.latest(client=authed_client)

    assert weight_data is not None
    assert weight_data.weight == 907.0
    assert weight_data.source_type == "MANUAL"
    authed_client.connectapi.assert_called_once_with(
        "/weight-service/weight/latest", params={"ignorePriority": "true"}
    )


def test_weight_latest_with_date_param(authed_client):
    fixture = load_fixture("weight_latest.json")
    authed_client.connectapi = Mock(return_value=fixture)

    weight_data = WeightData.latest(day=date(2026, 1, 1), client=authed_client)

    assert weight_data is not None
    assert weight_data.weight == 907.0
    authed_client.connectapi.assert_called_once_with(
        "/weight-service/weight/latest",
        params={"ignorePriority": "true", "date": "2026-01-01"},
    )


def test_weight_latest_returns_none_for_empty_response(authed_client):
    authed_client.connectapi = Mock(return_value=None)

    weight_data = WeightData.latest(client=authed_client)

    assert weight_data is None


def test_weight_latest_returns_none_for_empty_dict(authed_client):
    authed_client.connectapi = Mock(return_value={})

    weight_data = WeightData.latest(client=authed_client)

    assert weight_data is None


def test_weight_create_constructs_correct_request(authed_client):
    authed_client.connectapi = Mock(return_value=None)

    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    WeightData.create(weight=85000, timestamp=ts, client=authed_client)

    authed_client.connectapi.assert_called_once_with(
        "/weight-service/user-weight",
        method="POST",
        json={
            "dateTimestamp": "2026-01-01T00:00:00.00",
            "gmtTimestamp": "2026-01-01T00:00:00.00",
            "unitKey": "kg",
            "value": 85000,
        },
    )


def test_weight_create_without_date_param(authed_client):
    authed_client.connectapi = Mock(return_value=None)

    WeightData.create(weight=85000, client=authed_client)

    call_args = authed_client.connectapi.call_args
    assert call_args[0][0] == "/weight-service/user-weight"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["json"]["value"] == 85000
    assert call_args[1]["json"]["unitKey"] == "kg"
