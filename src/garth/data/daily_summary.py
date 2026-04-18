from datetime import date

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .. import http
from ..utils import camel_to_snake_dict, format_end_date
from ._base import Data


@dataclass
class DailySummary(Data):
    """Daily wellness summary aggregating key health metrics."""

    user_profile_id: int
    calendar_date: date
    total_kilocalories: int | None = None
    active_kilocalories: int | None = None
    total_steps: int | None = None
    total_distance_meters: int | None = None
    min_heart_rate: int | None = None
    max_heart_rate: int | None = None
    min_avg_heart_rate: int | None = None
    max_avg_heart_rate: int | None = None
    resting_heart_rate: int | None = None
    last_seven_days_avg_resting_heart_rate: int | None = None
    max_stress_level: int | None = None
    average_stress_level: int | None = None
    stress_qualifier: str | None = None
    body_battery_at_wake_time: int | None = None
    body_battery_highest_value: int | None = None
    body_battery_lowest_value: int | None = None
    moderate_intensity_minutes: int | None = None
    vigorous_intensity_minutes: int | None = None
    active_seconds: int | None = None
    highly_active_seconds: int | None = None
    sedentary_seconds: int | None = None
    sleeping_seconds: int | None = None
    floors_ascended: float | None = None
    floors_descended: float | None = None
    average_spo_2: int | None = None
    lowest_spo_2: int | None = None
    avg_waking_respiration_value: int | None = None
    highest_respiration_value: int | None = None
    lowest_respiration_value: int | None = None

    @classmethod
    def get(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Get daily wellness summary for a given day.

        Args:
            day: Target date (defaults to today)
            client: Optional HTTP client (uses default if not provided)

        Returns:
            DailySummary instance or None if no data
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/usersummary-service/usersummary/daily/?calendarDate={day}"
        daily_summary = client.connectapi(path)

        if not daily_summary:
            return None  # pragma: no cover

        assert isinstance(daily_summary, dict), (
            f"Expected dict from {path}, got {type(daily_summary).__name__}"
        )
        daily_summary = camel_to_snake_dict(daily_summary)
        return cls(**daily_summary)

    @classmethod
    def stats_by_type(
        cls,
        day: date | str | None = None,
        stats_type: str = "STEPS",
        *,
        client: http.Client | None = None,
    ) -> dict | None:
        """Get daily stats by type.

        Args:
            day: Date to query (defaults to today)
            stats_type: Type of stats e.g. "STEPS", "CALORIES"
            client: Optional HTTP client

        Returns:
            Dictionary of stats or None if no data available
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/usersummary-service/stats/daily/{day}/{day}"
        data = client.connectapi(path, params={"statsType": stats_type})

        if not data:
            return None

        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        return camel_to_snake_dict(data)

    @classmethod
    def wellness_chart(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> dict | list | None:
        """Get wellness summary chart data.

        Args:
            day: Date to query (defaults to today)
            client: Optional HTTP client

        Returns:
            List of wellness chart data or None if no data available
        """
        client = client or http.client
        day = format_end_date(day)
        path = "/wellness-service/wellness/dailySummaryChart"
        data = client.connectapi(path, params={"date": str(day)})

        if data is None:
            return None

        return data
