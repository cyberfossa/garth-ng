from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

from freezegun import freeze_time

from garth.data import WeightData
from garth.fit import build_body_composition
from garth.http import Client


def decode_fit_weight_scale(fit_bytes: bytes) -> dict:
    """Decode FIT bytes and return the first weight_scale message."""
    from garmin_fit_sdk import Decoder, Stream

    stream = Stream.from_byte_array(bytearray(fit_bytes))
    messages, errors = Decoder(stream).read()
    assert not errors
    return messages["weight_scale_mesgs"][0]


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


def test_weight_create_without_date_param(authed_client):
    authed_client.connectapi = Mock(return_value=None)

    WeightData.create(weight=85.0, client=authed_client)

    call_args = authed_client.connectapi.call_args
    assert call_args[0][0] == "/weight-service/user-weight"
    assert call_args[1]["method"] == "POST"
    assert call_args[1]["json"]["value"] == 85.0
    assert call_args[1]["json"]["unitKey"] == "kg"


def test_weight_create_cassette(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_weight_create.yaml",
    )
    WeightData.create(
        weight=72.5,
        timestamp=datetime(2026, 4, 10, 14, 30),
        client=authed_client,
    )


def test_weight_delete_constructs_correct_request(authed_client):
    authed_client.connectapi = Mock(return_value=None)

    WeightData.delete(
        sample_pk=12345, day=date(2026, 1, 15), client=authed_client
    )

    authed_client.connectapi.assert_called_once_with(
        "/weight-service/weight/2026-01-15/byversion/12345",
        method="DELETE",
    )


def test_weight_delete_without_day_uses_today(authed_client):
    authed_client.connectapi = Mock(return_value=None)

    WeightData.delete(sample_pk=99999, client=authed_client)

    call_args = authed_client.connectapi.call_args
    assert call_args[0][0].startswith("/weight-service/weight/")
    assert call_args[0][0].endswith("/byversion/99999")
    assert call_args[1]["method"] == "DELETE"


def test_build_body_composition_fit_roundtrip():
    from garmin_fit_sdk import Decoder, Stream

    ts = datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc)
    fit_bytes = build_body_composition(
        weight=75.5,
        timestamp=ts,
        percent_fat=22.5,
        percent_hydration=58.0,
        muscle_mass=58.5,
        bone_mass=3.2,
        bmi=23.3,
        basal_met=1800,
        active_met=2200,
        metabolic_age=32,
        physique_rating=5,
        visceral_fat_mass=8.5,
        visceral_fat_rating=12,
    )

    assert isinstance(fit_bytes, bytes)
    stream = Stream.from_byte_array(bytearray(fit_bytes))
    messages, errors = Decoder(stream).read()
    assert not errors
    assert messages["file_id_mesgs"][0]["type"] == "weight"

    ws = decode_fit_weight_scale(fit_bytes)
    assert ws["weight"] == 7550
    assert abs(ws["percent_fat"] - 22.5) < 0.1
    assert abs(ws["percent_hydration"] - 58.0) < 0.1
    assert abs(ws["muscle_mass"] - 58.5) < 0.1
    assert abs(ws["bone_mass"] - 3.2) < 0.1
    assert abs(ws["bmi"] - 23.3) < 0.1
    assert ws["metabolic_age"] == 32
    assert ws["physique_rating"] == 5
    assert ws["visceral_fat_rating"] == 12
    assert abs(ws["basal_met"] - 1800) < 1
    assert abs(ws["active_met"] - 2200) < 1
    assert abs(ws["visceral_fat_mass"] - 8.5) < 0.1


def test_build_body_composition_fit_weight_only():
    ts = datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc)
    fit_bytes = build_body_composition(weight=80.0, timestamp=ts)

    assert isinstance(fit_bytes, bytes)
    assert len(fit_bytes) > 12

    ws = decode_fit_weight_scale(fit_bytes)
    assert "percent_fat" not in ws or ws["percent_fat"] is None
    assert "muscle_mass" not in ws or ws["muscle_mass"] is None


def test_create_body_composition_calls_upload(authed_client):
    with patch.object(authed_client, "upload", Mock(return_value=None)):
        WeightData.create_body_composition(
            weight=75.5,
            percent_fat=22.5,
            client=authed_client,
        )

        assert authed_client.upload.called
        fp = authed_client.upload.call_args[0][0]
        assert fp.name == "body_composition.fit"
        fp.seek(0)
        data = fp.read()
        assert data[8:12] == b".FIT"
        assert len(data) > 12


@freeze_time("2026-04-10 12:00:00")
def test_create_body_composition_default_timestamp(authed_client):
    authed_client.upload = Mock(return_value=None)
    WeightData.create_body_composition(weight=70.0, client=authed_client)

    assert authed_client.upload.called
    fp = authed_client.upload.call_args[0][0]
    fp.seek(0)
    ws = decode_fit_weight_scale(fp.read())
    assert ws.get("timestamp") is not None


def test_create_body_composition_upload_full(authed_client):
    authed_client.upload = Mock(
        return_value={"detailedImportResult": {"successes": []}}
    )
    WeightData.create_body_composition(
        weight=72.5,
        percent_fat=20.0,
        muscle_mass=55.0,
        timestamp=datetime(2026, 4, 10, 14, 30, tzinfo=timezone.utc),
        client=authed_client,
    )

    assert authed_client.upload.called
    fp = authed_client.upload.call_args[0][0]
    fp.seek(0)
    ws = decode_fit_weight_scale(fp.read())
    assert abs(ws["percent_fat"] - 20.0) < 0.1
    assert abs(ws["muscle_mass"] - 55.0) < 0.1
