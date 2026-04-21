from __future__ import annotations

from datetime import date

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .. import http
from ..utils import camel_to_snake_dict, format_end_date


@dataclass
class WeightGoal:
    """Weight goal data for a given day."""

    user_goals: list | None = None
    user_goal_ranges: dict | None = None

    @classmethod
    def get(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Get weight goal data for a given day.

        Args:
            day: Target date (defaults to today)
            client: Optional HTTP client (uses default if not provided)

        Returns:
            WeightGoal instance or None if no data
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/goal-service/goal/user/effective/weightgoal/{day}/{day}"
        data = client.connectapi(path)

        if not data:
            return None

        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        data = camel_to_snake_dict(data)
        return cls(**data)
