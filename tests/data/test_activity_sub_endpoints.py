from unittest.mock import MagicMock

from tests.fixture_helpers import load_fixture

from garth.data.activity import (
    Activity,
    ActivityDetails,
    ActivityMapDetails,
    ActivityRounds,
    ActivityType,
    ActivityWorkout,
    ExerciseSets,
    HrTimeInZone,
)


def _mock_client(return_value):
    client = MagicMock()
    client.connectapi.return_value = return_value
    return client


def test_activity_details():
    fixture = load_fixture("activity_details.json")
    client = _mock_client(fixture)
    result = Activity.details(12345, client=client)
    assert isinstance(result, ActivityDetails)
    assert result.activity_id == fixture["activityId"]
    assert result.details_available == fixture["detailsAvailable"]
    client.connectapi.assert_called_once()
    call_path = client.connectapi.call_args[0][0]
    assert "/activity-service/activity/12345/details" in call_path
    assert "maxChartSize=1400" in call_path


def test_activity_details_custom_chart_size():
    fixture = load_fixture("activity_details.json")
    client = _mock_client(fixture)
    Activity.details(12345, max_chart_size=500, client=client)
    call_path = client.connectapi.call_args[0][0]
    assert "maxChartSize=500" in call_path


def test_activity_exercise_sets():
    fixture = load_fixture("activity_exercise_sets.json")
    client = _mock_client(fixture)
    result = Activity.exercise_sets(22421146451, client=client)
    assert isinstance(result, ExerciseSets)
    assert result.activity_id == fixture["activityId"]
    assert result.exercise_sets == fixture["exerciseSets"]
    client.connectapi.assert_called_once_with(
        "/activity-service/activity/22421146451/exerciseSets"
    )


def test_activity_hr_time_in_zones():
    fixture = load_fixture("activity_hr_time_in_zones.json")
    client = _mock_client(fixture)
    result = Activity.hr_time_in_zones(12345, client=client)
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, HrTimeInZone)
    client.connectapi.assert_called_once_with(
        "/activity-service/activity/12345/hrTimeInZones"
    )


def test_activity_map_details():
    fixture = load_fixture("activity_map_details.json")
    client = _mock_client(fixture)
    result = Activity.map_details(22421146451, client=client)
    assert isinstance(result, ActivityMapDetails)
    assert result.g_polyline is not None
    assert result.g_polyline.activity_id == 22421146451
    assert result.g_polyline.number_of_points == 0
    client.connectapi.assert_called_once_with(
        "/activity-service/activity/22421146451/details/mapdetails"
    )


def test_activity_rounds():
    fixture = load_fixture("activity_rounds.json")
    client = _mock_client(fixture)
    result = Activity.rounds(22421146451, client=client)
    assert isinstance(result, ActivityRounds)
    assert result.activity_id == fixture["activityId"]
    assert result.activity_uuid is not None
    assert result.activity_uuid.uuid == "5596e4b9-8497-470e-aa3e-baa4f906a0c2"
    assert result.rounds == []
    client.connectapi.assert_called_once_with(
        "/activity-service/activity/22421146451/rounds"
    )


def test_activity_workouts():
    fixture = load_fixture("activity_workouts.json")
    client = _mock_client(fixture)
    result = Activity.workouts(12345, client=client)
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, ActivityWorkout)
    client.connectapi.assert_called_once_with(
        "/activity-service/activity/12345/workouts"
    )


def test_activity_types():
    fixture = load_fixture("activity_types.json")
    client = _mock_client(fixture)
    result = Activity.activity_types(client=client)
    assert isinstance(result, list)
    assert len(result) == len(fixture)
    for item in result:
        assert isinstance(item, ActivityType)
    first = result[0]
    assert first.type_id == 1
    assert first.type_key == "running"
    assert first.parent_type_id == 17
    client.connectapi.assert_called_once_with(
        "/activity-service/activity/activityTypes"
    )
