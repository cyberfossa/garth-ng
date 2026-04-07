from datetime import date, datetime, timedelta, timezone

from garth.data import WeightData
from garth.http import Client


def test_weight_data_timestamps_preserved(
    authed_client: Client, load_cassette
):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_weight_data_timestamps_preserved.yaml",
    )
    weight_data = WeightData.get(date(2025, 6, 15), client=authed_client)
    assert weight_data is not None

    assert isinstance(weight_data.timestamp_gmt, int)
    assert isinstance(weight_data.timestamp_local, int)
    assert weight_data.timestamp_gmt == 1749996876000
    assert weight_data.timestamp_local == 1749975276000

    expected_utc = datetime.fromtimestamp(
        weight_data.timestamp_gmt / 1000, tz=timezone.utc
    )
    assert weight_data.datetime_utc == expected_utc
    assert weight_data.datetime_local.tzinfo is not None


def test_get_daily_weight_data(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_get_daily_weight_data.yaml",
    )
    weight_data = WeightData.get(date(2025, 6, 15), client=authed_client)
    assert weight_data is not None
    assert weight_data.source_type == "INDEX_SCALE"
    assert weight_data.weight is not None
    assert weight_data.bmi is not None
    assert weight_data.body_fat is not None
    assert weight_data.body_water is not None
    assert weight_data.bone_mass is not None
    assert weight_data.muscle_mass is not None
    assert weight_data.datetime_local.tzinfo == timezone(timedelta(hours=-6))
    assert weight_data.datetime_utc.tzinfo == timezone.utc


def test_get_manual_weight_data(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_get_manual_weight_data.yaml",
    )
    weight_data = WeightData.get(date(2025, 6, 14), client=authed_client)
    assert weight_data is not None
    assert weight_data.source_type == "MANUAL"
    assert weight_data.weight is not None
    assert weight_data.bmi is None
    assert weight_data.body_fat is None
    assert weight_data.body_water is None
    assert weight_data.bone_mass is None
    assert weight_data.muscle_mass is None


def test_get_nonexistent_weight_data(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_get_nonexistent_weight_data.yaml",
    )
    weight_data = WeightData.get(date(2020, 1, 1), client=authed_client)
    assert weight_data is None


def test_weight_data_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_weight_data_list.yaml",
    )
    end = date(2025, 6, 15)
    days = 15
    weight_data = WeightData.list(end, days, client=authed_client)

    assert len(weight_data) == 4
    assert all(isinstance(data, WeightData) for data in weight_data)
    assert all(
        weight_data[i].datetime_utc <= weight_data[i + 1].datetime_utc
        for i in range(len(weight_data) - 1)
    )


def test_weight_data_list_single_day(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_weight_data_list_single_day.yaml",
    )
    end = date(2025, 6, 14)
    weight_data = WeightData.list(end, client=authed_client)
    assert len(weight_data) == 2
    assert all(isinstance(data, WeightData) for data in weight_data)
    assert weight_data[0].source_type == "INDEX_SCALE"
    assert weight_data[1].source_type == "MANUAL"


def test_weight_data_list_empty(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_weight_data_list_empty.yaml",
    )
    end = date(2020, 1, 1)
    days = 15
    weight_data = WeightData.list(end, days, client=authed_client)
    assert len(weight_data) == 0
