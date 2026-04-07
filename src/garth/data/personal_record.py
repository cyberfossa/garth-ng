from __future__ import annotations

import builtins

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .. import http
from ..utils import camel_to_snake_dict


@dataclass
class PersonalRecord:
    """Garmin Connect personal record data.

    Retrieve all personal records or filter by activity ID.

    Example:
        >>> records = PersonalRecord.list()
        >>> len(records)
        2

        >>> activity_records = PersonalRecord.for_activity(22421146451)
        >>> len(activity_records)
        2
    """

    id: int
    type_id: int
    status: str | None = None
    activity_id: int | None = None
    activity_name: str | None = None
    activity_type: str | None = None
    activity_start_date_time_in_gmt: int | None = None
    act_start_date_time_in_gmt_formatted: str | None = None
    activity_start_date_time_local: int | None = None
    activity_start_date_time_local_formatted: str | None = None
    value: float | None = None
    pr_start_time_gmt: int | None = None
    pr_start_time_gmt_formatted: str | None = None
    pr_start_time_local: int | None = None
    pr_start_time_local_formatted: str | None = None
    pr_type_label_key: str | None = None
    pool_length_unit: str | None = None

    @classmethod
    def list(cls, *, client: http.Client | None = None) -> builtins.list[Self]:
        """List all personal records.

        Args:
            client: Optional HTTP client (uses default if not provided)

        Returns:
            List of PersonalRecord instances
        """
        client = client or http.client
        items = client.connectapi("/personalrecord-service/personalrecord")
        assert isinstance(items, list), (
            f"Expected list, got {type(items).__name__}"
        )
        return [cls(**camel_to_snake_dict(item)) for item in items]

    @classmethod
    def for_activity(
        cls, activity_id: int, *, client: http.Client | None = None
    ) -> builtins.list[Self]:
        """Get personal records for a specific activity.

        Args:
            activity_id: The Garmin activity ID
            client: Optional HTTP client (uses default if not provided)

        Returns:
            List of PersonalRecord instances for the activity
        """
        client = client or http.client
        path = "/personalrecord-service/personalrecord/prByActivityId/"
        path = f"{path}{activity_id}"
        items = client.connectapi(path)
        assert isinstance(items, list), (
            f"Expected list, got {type(items).__name__}"
        )
        return [cls(**camel_to_snake_dict(item)) for item in items]


@dataclass
class PersonalRecordType:
    """Garmin Connect personal record type data.

    Retrieve all available personal record types.

    Example:
        >>> types = PersonalRecordType.list()
        >>> len(types)
        51
    """

    id: int
    key: str
    visible: bool | None = None
    sport: str | None = None
    min_value: float | None = None
    max_value: float | None = None

    @classmethod
    def list(cls, *, client: http.Client | None = None) -> builtins.list[Self]:
        """List all personal record types.

        Args:
            client: Optional HTTP client (uses default if not provided)

        Returns:
            List of PersonalRecordType instances
        """
        client = client or http.client
        items = client.connectapi("/personalrecord-service/personalrecordtype")
        assert isinstance(items, list), (
            f"Expected list, got {type(items).__name__}"
        )
        return [cls(**camel_to_snake_dict(item)) for item in items]
