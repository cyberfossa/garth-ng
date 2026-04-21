from unittest.mock import MagicMock

from garth import PersonalRecord
from garth.data.personal_record import PersonalRecordType
from garth.http import Client
from tests.fixture_helpers import load_fixture


def test_personal_record_list(authed_client: Client) -> None:
    """Test PersonalRecord.list() parses fixture data."""
    fixture = load_fixture("personal_record_list.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    records = PersonalRecord.list(client=authed_client)

    assert isinstance(records, list)
    assert len(records) == 2
    assert all(isinstance(r, PersonalRecord) for r in records)

    # Check first record
    assert records[0].id == 2891221107
    assert records[0].type_id == 2
    assert records[0].status == "ACCEPTED"
    assert records[0].activity_id == 22421146451
    assert records[0].value == 3600.0

    authed_client.connectapi.assert_called_once_with(
        "/personalrecord-service/personalrecord"
    )


def test_personal_record_for_activity(authed_client: Client) -> None:
    """Test PersonalRecord.for_activity() parses fixture data."""
    activity_id = 22421146451
    fixture = load_fixture("personal_record_for_activity.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    records = PersonalRecord.for_activity(activity_id, client=authed_client)

    assert isinstance(records, list)
    assert len(records) == 2
    assert all(isinstance(r, PersonalRecord) for r in records)

    # Check first record has pr_type_label_key field populated
    assert records[0].pr_type_label_key == "pr.label.1mile.run"
    assert records[1].pr_type_label_key == "pr.label.farthest.run"

    authed_client.connectapi.assert_called_once_with(
        f"/personalrecord-service/personalrecord/prByActivityId/{activity_id}"
    )


def test_personal_record_type_list(authed_client: Client) -> None:
    """Test PersonalRecordType.list() parses fixture data."""
    fixture = load_fixture("personal_record_types.json")
    authed_client.connectapi = MagicMock(return_value=fixture)
    types = PersonalRecordType.list(client=authed_client)

    assert isinstance(types, list)
    assert len(types) == 51
    assert all(isinstance(t, PersonalRecordType) for t in types)

    # Check first record
    assert types[0].id == 1
    assert types[0].key == "pr.label.1k.run"
    assert types[0].visible is True
    assert types[0].sport == "RUNNING"
    assert types[0].min_value == 995.0
    assert types[0].max_value == 1016.0

    authed_client.connectapi.assert_called_once_with(
        "/personalrecord-service/personalrecordtype"
    )
