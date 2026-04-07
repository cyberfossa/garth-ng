from datetime import date

from garth import MorningTrainingReadinessData
from garth.http import Client


def test_morning_training_readiness_data_get(
    authed_client: Client, load_cassette
):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_morning_training_readiness_data_get.yaml",
    )
    morning_training_readiness_data = MorningTrainingReadinessData.get(
        "2025-07-07", client=authed_client
    )
    assert morning_training_readiness_data
    assert morning_training_readiness_data.calendar_date == date(2025, 7, 7)
    assert morning_training_readiness_data.score
    assert morning_training_readiness_data.acute_load
    assert morning_training_readiness_data.sleep_history_factor_percent

    morning_training_readiness_data_none = MorningTrainingReadinessData.get(
        "2024-07-07", client=authed_client
    )
    assert morning_training_readiness_data_none is None


def test_morning_training_readiness_data_list(
    authed_client: Client, load_cassette
):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_morning_training_readiness_data_list.yaml",
    )
    days = 2
    end = date(2025, 7, 7)
    morning_training_readiness = MorningTrainingReadinessData.list(
        end, days, client=authed_client, max_workers=1
    )
    assert len(morning_training_readiness) == days
    assert morning_training_readiness[-1].calendar_date == end
