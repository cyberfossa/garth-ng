from datetime import date

from garth import GarminScoresData
from garth.http import Client


def test_garmin_scores_data_get(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_garmin_scores_data_get.yaml",
    )
    garmin_scores_data = GarminScoresData.get(
        "2025-07-07", client=authed_client
    )
    assert garmin_scores_data
    assert garmin_scores_data.calendar_date == date(2025, 7, 7)
    assert garmin_scores_data.vo_2_max
    assert garmin_scores_data.endurance_score
    assert garmin_scores_data.hill_score

    garmin_scores_data_none = GarminScoresData.get(
        "2024-07-07", client=authed_client
    )
    assert garmin_scores_data_none is None


def test_garmin_scores_data_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_garmin_scores_data_list.yaml",
    )
    days = 2
    end = date(2025, 7, 7)
    garmin_scores = GarminScoresData.list(
        end, days, client=authed_client, max_workers=1
    )
    assert len(garmin_scores) == days
    assert garmin_scores[-1].calendar_date == end
