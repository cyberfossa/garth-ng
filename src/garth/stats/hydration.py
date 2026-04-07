from datetime import date, datetime
from typing import ClassVar

from pydantic.dataclasses import dataclass

from .. import http
from ..utils import camel_to_snake_dict, format_end_date
from ._base import Stats


BASE_PATH = "/usersummary-service/stats/hydration"


@dataclass
class HydrationLogEntry:
    user_id: int
    calendar_date: date
    value_in_ml: float
    last_entry_timestamp_local: datetime
    goal_in_ml: float | None = None
    daily_averagein_ml: float | None = None
    sweat_loss_in_ml: float | None = None
    activity_intake_in_ml: float | None = None


@dataclass
class DailyHydration(Stats):
    value_in_ml: float
    goal_in_ml: float

    _path: ClassVar[str] = f"{BASE_PATH}/daily/{{start}}/{{end}}"
    _page_size: ClassVar[int] = 28

    @staticmethod
    def log(
        value_in_ml: float,
        *,
        timestamp: datetime | None = None,
        client: http.Client | None = None,
    ) -> HydrationLogEntry:
        """Log hydration intake.

        Args:
            value_in_ml: Amount of water in milliliters
            timestamp: When the hydration was logged (defaults to now)
            client: Optional HTTP client

        Returns:
            HydrationLogEntry with updated hydration data
        """
        client = client or http.client
        if timestamp is None:
            timestamp = datetime.now()

        profile_id = client.user_profile["profileId"]
        response = client.connectapi(
            "/usersummary-service/usersummary/hydration/log",
            method="PUT",
            json={
                "valueInML": str(value_in_ml),
                "timestampLocal": timestamp.strftime("%Y-%m-%dT%H:%M:%S.0"),
                "userProfileId": str(profile_id),
            },
        )
        assert isinstance(response, dict)
        return HydrationLogEntry(**camel_to_snake_dict(response))

    @classmethod
    def weekly(
        cls,
        day: date | str | None = None,
        *,
        weeks: int = 52,
        client: http.Client | None = None,
    ) -> list:
        """Get weekly hydration summaries.

        Args:
            day: End date
            weeks: Number of weeks to retrieve
            client: Optional HTTP client

        Returns:
            List of weekly hydration data
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"{BASE_PATH}/weekly/{day}/{weeks}"
        data = client.connectapi(path)
        if not data:
            return []
        assert isinstance(data, list), (
            f"Expected list from {path}, got {type(data).__name__}"
        )
        return data

    @classmethod
    def all_data(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> dict | None:
        """Get all hydration data for a day.

        Args:
            day: Date to query
            client: Optional HTTP client

        Returns:
            Detailed hydration data dict or None
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/usersummary-service/usersummary/hydration/allData/{day}"
        data = client.connectapi(path)
        if not data:
            return None
        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        return camel_to_snake_dict(data)
