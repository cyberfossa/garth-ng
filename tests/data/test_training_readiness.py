from datetime import date

from garth import TrainingReadinessData
from garth.http import Client


def test_training_readiness_data_get(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_training_readiness_data_get.yaml",
    )
    entries = TrainingReadinessData.get("2025-07-07", client=authed_client)
    assert entries is not None
    assert len(entries) >= 1
    assert all(e.calendar_date == date(2025, 7, 7) for e in entries)

    contexts = {e.input_context for e in entries}
    assert "AFTER_WAKEUP_RESET" in contexts

    morning_entry = next(
        e for e in entries if e.input_context == "AFTER_WAKEUP_RESET"
    )
    assert morning_entry.score is not None
    assert morning_entry.level is not None
    assert morning_entry.valid_sleep is True

    entries_none = TrainingReadinessData.get(
        "2030-01-01", client=authed_client
    )
    assert entries_none is None


def test_training_readiness_data_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_training_readiness_data_list.yaml",
    )
    days = 2
    end = date(2025, 7, 7)
    entries = TrainingReadinessData.list(
        end, days, client=authed_client, max_workers=1
    )
    assert len(entries) >= days
    for i in range(len(entries) - 1):
        assert (entries[i].calendar_date, entries[i].timestamp) <= (
            entries[i + 1].calendar_date,
            entries[i + 1].timestamp,
        )
