import pytest

from garth import Activity
from garth.http import Client


def test_activity_list(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_activity_list.yaml",
    )
    activities = Activity.list(limit=3, client=authed_client)
    assert len(activities) == 3
    for activity in activities:
        assert activity.activity_id
        assert activity.activity_name
        assert activity.activity_type
        assert activity.activity_type.type_key


def test_activity_get(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_activity_get.yaml",
    )
    activities = Activity.list(limit=1, client=authed_client)
    assert len(activities) == 1
    activity_id = activities[0].activity_id

    activity = Activity.get(activity_id, client=authed_client)
    assert activity.activity_id == activity_id
    assert activity.activity_name
    assert activity.activity_type
    assert activity.activity_type.type_key
    assert activity.summary is not None
    assert activity.summary.distance is not None or activity.summary.duration


def test_activity_list_pagination(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/data/cassettes/test_activity_list_pagination.yaml",
    )
    page1 = Activity.list(limit=2, start=0, client=authed_client)
    page2 = Activity.list(limit=2, start=2, client=authed_client)

    assert len(page1) == 2
    assert len(page2) == 2
    page1_ids = {a.activity_id for a in page1}
    page2_ids = {a.activity_id for a in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_activity_update_validation():
    with pytest.raises(ValueError, match="At least one of"):
        Activity.update(123)


@pytest.mark.parametrize(
    "name,description,cassette_suffix",
    [
        ("Test Name Only", None, "name_only"),
        (None, "Test description only", "description_only"),
        ("Test Both", "Test both description", "both"),
    ],
    ids=["name_only", "description_only", "both"],
)
def test_activity_update(
    authed_client: Client,
    load_cassette,
    name: str | None,
    description: str | None,
    cassette_suffix: str,
):
    load_cassette(
        authed_client,
        f"tests/data/cassettes/test_activity_update[{cassette_suffix}].yaml",
    )
    activity_id = 21522899847

    Activity.update(
        activity_id,
        name=name,
        description=description,
        client=authed_client,
    )

    updated = Activity.get(activity_id, client=authed_client)
    if name is not None:
        assert updated.activity_name == name

    Activity.update(
        activity_id,
        name="Yoga",
        description="",
        client=authed_client,
    )
