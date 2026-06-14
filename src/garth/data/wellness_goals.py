from __future__ import annotations

from datetime import date

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .. import http
from ..utils import camel_to_snake_dict, format_end_date


@dataclass
class StepsGoal:
    """Steps goal data from wellness service."""

    device_goal: int | None = None
    user_goal: int | None = None
    synced_to_device: bool | None = None
    effective: str | None = None
    user_goal_category: str | None = None
    goal_type: str | None = None

    @classmethod
    def get(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Fetch steps goal for a specific date.

        Args:
            day: Target date (defaults to today)
            client: Optional HTTP client (uses global if not provided)

        Returns:
            StepsGoal instance or None if no data
        """
        client = client or http.client
        day = format_end_date(day)
        path = (
            f"/wellness-service/wellness/wellness-goals/"
            f"consolidated/steps/{day}"
        )
        data = client.connectapi(path)

        if not data:
            return None

        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        data = camel_to_snake_dict(data)
        return cls(**data)
