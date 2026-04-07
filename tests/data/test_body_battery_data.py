from datetime import date
from unittest.mock import MagicMock

from garth import BodyBatteryData, DailyBodyBatteryStress
from garth.http import Client


def test_body_battery_data_get(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_body_battery_data_get.yaml",
    )
    body_battery_data = BodyBatteryData.get("2023-07-20", client=authed_client)
    assert isinstance(body_battery_data, list)

    if body_battery_data:
        event = body_battery_data[0]
        assert event is not None

        readings = event.body_battery_readings
        assert isinstance(readings, list)

        if readings:
            reading = readings[0]
            assert hasattr(reading, "timestamp")
            assert hasattr(reading, "status")
            assert hasattr(reading, "level")
            assert hasattr(reading, "version")

            assert event.current_level is not None and isinstance(
                event.current_level, int
            )
            assert event.max_level is not None and isinstance(
                event.max_level, int
            )
            assert event.min_level is not None and isinstance(
                event.min_level, int
            )


def test_body_battery_data_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_body_battery_data_list.yaml",
    )
    days = 3
    end = date(2023, 7, 20)
    body_battery_data = BodyBatteryData.list(end, days, client=authed_client)
    assert isinstance(body_battery_data, list)

    assert len(body_battery_data) >= 0


def test_daily_body_battery_stress_get(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_daily_body_battery_stress_get.yaml",
    )
    daily_data = DailyBodyBatteryStress.get("2023-07-20", client=authed_client)

    if daily_data:
        assert daily_data.user_profile_pk
        assert daily_data.calendar_date == date(2023, 7, 20)
        assert daily_data.start_timestamp_gmt
        assert daily_data.end_timestamp_gmt

        assert isinstance(daily_data.max_stress_level, int)
        assert isinstance(daily_data.avg_stress_level, int)
        assert isinstance(daily_data.stress_values_array, list)
        assert isinstance(daily_data.body_battery_values_array, list)

        stress_readings = daily_data.stress_readings
        assert isinstance(stress_readings, list)

        if stress_readings:
            stress_reading = stress_readings[0]
            assert hasattr(stress_reading, "timestamp")
            assert hasattr(stress_reading, "stress_level")

        bb_readings = daily_data.body_battery_readings
        assert isinstance(bb_readings, list)

        if bb_readings:
            bb_reading = bb_readings[0]
            assert hasattr(bb_reading, "timestamp")
            assert hasattr(bb_reading, "status")
            assert hasattr(bb_reading, "level")
            assert hasattr(bb_reading, "version")

            assert daily_data.current_body_battery is not None and isinstance(
                daily_data.current_body_battery, int
            )
            assert daily_data.max_body_battery is not None and isinstance(
                daily_data.max_body_battery, int
            )
            assert daily_data.min_body_battery is not None and isinstance(
                daily_data.min_body_battery, int
            )

            if len(bb_readings) >= 2:
                change = daily_data.body_battery_change
                assert change is not None


def test_daily_body_battery_stress_get_no_data(
    authed_client: Client, load_cassette
):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_daily_body_battery_stress_get_no_data.yaml",
    )
    daily_data = DailyBodyBatteryStress.get("2020-01-01", client=authed_client)

    assert daily_data is None or isinstance(daily_data, DailyBodyBatteryStress)


def test_daily_body_battery_stress_get_incomplete_data(
    authed_client: Client, load_cassette
):
    load_cassette(
        authed_client,
        "tests/data/cassettes/"
        "test_daily_body_battery_stress_get_incomplete_data.yaml",
    )
    daily_data = DailyBodyBatteryStress.get("2025-12-18", client=authed_client)
    assert daily_data
    assert all(r.level is not None for r in daily_data.body_battery_readings)
    assert all(r.status is not None for r in daily_data.body_battery_readings)


def test_daily_body_battery_stress_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_daily_body_battery_stress_list.yaml",
    )
    days = 3
    end = date(2023, 7, 20)
    daily_data_list = DailyBodyBatteryStress.list(
        end, days, client=authed_client, max_workers=1
    )
    assert isinstance(daily_data_list, list)
    assert len(daily_data_list) <= days

    for daily_data in daily_data_list:
        assert isinstance(daily_data, DailyBodyBatteryStress)
        assert isinstance(daily_data.calendar_date, date)
        assert daily_data.user_profile_pk


def test_body_battery_properties_edge_cases(
    authed_client: Client, load_cassette
):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_body_battery_properties_edge_cases.yaml",
    )
    daily_data = DailyBodyBatteryStress.get("2023-07-20", client=authed_client)

    if daily_data:
        if not daily_data.body_battery_values_array:
            assert daily_data.body_battery_readings == []
            assert daily_data.current_body_battery is None
            assert daily_data.max_body_battery is None
            assert daily_data.min_body_battery is None
            assert daily_data.body_battery_change is None

        if not daily_data.stress_values_array:
            assert daily_data.stress_readings == []


def test_body_battery_data_get_api_error():
    mock_client = MagicMock()
    mock_client.connectapi.side_effect = Exception("API Error")

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert result == []


def test_body_battery_data_get_invalid_response():
    mock_client = MagicMock()
    mock_client.connectapi.return_value = {"error": "Invalid response"}

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert result == []


def test_body_battery_data_get_missing_event_data():
    mock_client = MagicMock()
    mock_client.connectapi.return_value = [
        {"activityName": "Test", "averageStress": 25}
    ]

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert len(result) == 1
    assert result[0].event is None


def test_body_battery_data_get_missing_event_start_time():
    mock_client = MagicMock()
    mock_client.connectapi.return_value = [
        {
            "event": {"eventType": "sleep"},
            "activityName": "Test",
            "averageStress": 25,
        }
    ]

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert result == []


def test_body_battery_data_get_invalid_datetime_format():
    mock_client = MagicMock()
    mock_client.connectapi.return_value = [
        {
            "event": {
                "eventType": "sleep",
                "eventStartTimeGmt": "invalid-date",
            },
            "activityName": "Test",
            "averageStress": 25,
        }
    ]

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert result == []


def test_body_battery_data_get_invalid_field_types():
    mock_client = MagicMock()
    mock_client.connectapi.return_value = [
        {
            "event": {
                "eventType": "sleep",
                "eventStartTimeGmt": ("2023-07-20T10:00:00.000Z"),
                "timezoneOffset": "invalid",
                "durationInMilliseconds": "invalid",
                "bodyBatteryImpact": "invalid",
            },
            "activityName": "Test",
            "averageStress": "invalid",
            "stressValuesArray": "invalid",
            "bodyBatteryValuesArray": "invalid",
        }
    ]

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert len(result) == 1


def test_body_battery_data_get_validation_error():
    mock_client = MagicMock()
    mock_client.connectapi.return_value = [
        {
            "event": {
                "eventType": "sleep",
                "eventStartTimeGmt": ("2023-07-20T10:00:00.000Z"),
            },
        }
    ]

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].event is not None
    assert result[0].activity_name is None


def test_body_battery_data_get_mixed_valid_invalid():
    mock_client = MagicMock()
    mock_client.connectapi.return_value = [
        {
            "event": {
                "eventType": "sleep",
                "eventStartTimeGmt": ("2023-07-20T10:00:00.000Z"),
                "timezoneOffset": -25200000,
                "durationInMilliseconds": 28800000,
                "bodyBatteryImpact": 35,
                "feedbackType": "good_sleep",
                "shortFeedback": "Good sleep",
            },
            "activityName": None,
            "activityType": None,
            "activityId": None,
            "averageStress": 15.5,
            "stressValuesArray": [[1689811800000, 12]],
            "bodyBatteryValuesArray": [[1689811800000, "charging", 45, 1.0]],
        },
        {
            "event": {"eventType": "sleep"},
            "activityName": "Test",
        },
    ]

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert len(result) == 1
    assert result[0].event is not None


def test_body_battery_data_get_unexpected_error():
    mock_client = MagicMock()

    class ExceptionRaisingDict(dict):
        def get(self, key, default=None):
            if key == "activityName":
                raise RuntimeError("Unexpected error during object creation")
            return super().get(key, default)

    mock_response_item = ExceptionRaisingDict(
        {
            "event": {
                "eventType": "sleep",
                "eventStartTimeGmt": ("2023-07-20T10:00:00.000Z"),
                "timezoneOffset": -25200000,
                "durationInMilliseconds": 28800000,
                "bodyBatteryImpact": 35,
                "feedbackType": "good_sleep",
                "shortFeedback": "Good sleep",
            },
            "activityName": None,
            "activityType": None,
            "activityId": None,
            "averageStress": 15.5,
            "stressValuesArray": [[1689811800000, 12]],
            "bodyBatteryValuesArray": [[1689811800000, "charging", 45, 1.0]],
        }
    )

    mock_client.connectapi.return_value = [mock_response_item]

    result = BodyBatteryData.get("2023-07-20", client=mock_client)
    assert result == []
