from datetime import date

from garth import FitnessActivity
from garth.http import Client


def test_fitness_activity_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_fitness_activity_list.yaml",
    )
    activities = FitnessActivity.list(
        date(2026, 1, 12), days=7, client=authed_client
    )
    assert len(activities) > 0

    for i in range(len(activities) - 1):
        assert activities[i].start_local <= activities[i + 1].start_local

    for activity in activities:
        assert activity.activity_id > 0
        assert activity.start_local is not None
        assert activity.activity_type is not None

    coaching = [a for a in activities if a.workout_type == "ADAPTIVE_COACHING"]
    if coaching:
        assert coaching[0].adaptive_coaching_workout_status is not None
