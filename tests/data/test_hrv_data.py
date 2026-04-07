from datetime import date

from garth import HRVData
from garth.http import Client
from tests.helpers import load_cassette as read_cassette


def test_hrv_data_get(authed_client: Client, load_cassette):
    cassette_path = "tests/data/cassettes/test_hrv_data_get.yaml"
    interactions = read_cassette(cassette_path)
    assert any(
        "/hrv-service/hrv/" in interaction["request"].get("uri", "")
        for interaction in interactions
    )

    load_cassette(
        authed_client,
        cassette_path,
    )
    hrv_data = HRVData.get("2023-07-20", client=authed_client)
    assert hrv_data
    assert hrv_data.user_profile_pk
    assert hrv_data.hrv_summary.calendar_date == date(2023, 7, 20)

    assert HRVData.get("2021-07-20", client=authed_client) is None


def test_hrv_data_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_hrv_data_list.yaml",
    )
    days = 2
    end = date(2023, 7, 20)
    hrv_data = HRVData.list(end, days, client=authed_client, max_workers=1)
    assert len(hrv_data) == days
    assert hrv_data[-1].hrv_summary.calendar_date == end
