from __future__ import annotations

from datetime import date

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .. import http
from ..utils import camel_to_snake_dict, format_end_date


@dataclass
class NutritionLog:
    """Nutrition food log data for a given day."""

    meal_date: date
    day_start_time: str | None = None
    day_end_time: str | None = None
    meal_details: list | None = None
    logged_foods_with_serving_sizes: list | None = None

    @classmethod
    def get(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Get nutrition food log for a given day.

        Args:
            day: Target date (defaults to today)
            client: Optional HTTP client (uses default if not provided)

        Returns:
            NutritionLog instance or None if no data
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/nutrition-service/food/logs/{day}"
        data = client.connectapi(path)

        if not data:
            return None

        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        data = camel_to_snake_dict(data)
        return cls(**data)


@dataclass
class NutritionSettings:
    """Nutrition settings for a given day."""

    diet_key: str | None = None
    diet_id: int | None = None
    total_calorie_goal: int | None = None
    total_carbs_goal: int | None = None
    total_protein_goal: int | None = None
    total_fat_goal: int | None = None
    saturated_fat_goal: int | None = None
    sodium_goal: int | None = None
    fiber_goal: int | None = None
    water_goal: int | None = None
    cholesterol_goal: int | None = None

    @classmethod
    def get(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Get nutrition settings for a given day.

        Args:
            day: Target date (defaults to today)
            client: Optional HTTP client (uses default if not provided)

        Returns:
            NutritionSettings instance or None if no data
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/nutrition-service/settings/{day}"
        data = client.connectapi(path)

        if not data:
            return None

        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        data = camel_to_snake_dict(data)
        return cls(**data)


@dataclass
class NutritionStatus:
    """Current nutrition status."""

    current_status: str | None = None
    has_used_nutrition: bool | None = None
    has_used_mfp: bool | None = None

    @classmethod
    def get(
        cls,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Get current nutrition status.

        Args:
            client: Optional HTTP client (uses default if not provided)

        Returns:
            NutritionStatus instance or None if no data
        """
        client = client or http.client
        path = "/nutrition-service/user/nutritionCurrentStatus"
        data = client.connectapi(path)

        if not data:
            return None

        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        data = camel_to_snake_dict(data)
        return cls(**data)
