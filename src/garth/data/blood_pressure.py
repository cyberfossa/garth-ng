from __future__ import annotations

from datetime import date

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .. import http
from ..utils import camel_to_snake_dict, format_end_date


@dataclass
class BloodPressureReading:
    """Single blood pressure measurement."""

    systolic: int
    diastolic: int
    pulse: int | None = None
    measurement_timestamp_local: str | None = None
    measurement_timestamp: int | None = None


@dataclass
class BloodPressure:
    """Blood pressure data for a given day."""

    start_date: date
    end_date: date
    blood_pressure_measurements: list[BloodPressureReading] | None = None
    total_measurement_count: int | None = None
    elevated_measurement_count: int | None = None

    @classmethod
    def get(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Get blood pressure data for a given day.

        Args:
            day: Target date (defaults to today)
            client: Optional HTTP client (uses default if not provided)

        Returns:
            BloodPressure instance or None if no data
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/bloodpressure-service/bloodpressure/dayview/{day}"
        data = client.connectapi(path)

        if not data:
            return None

        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        data = camel_to_snake_dict(data)

        # Convert blood_pressure_measurements to BloodPressureReading objects
        if data.get("blood_pressure_measurements"):
            measurements = []
            for m in data["blood_pressure_measurements"]:
                measurements.append(
                    BloodPressureReading(**camel_to_snake_dict(m))
                )
            data["blood_pressure_measurements"] = measurements

        return cls(**data)

    @classmethod
    def create(
        cls,
        systolic: int,
        diastolic: int,
        pulse: int | None = None,
        measurement_timestamp_local: str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        """Create a new blood pressure measurement.

        Args:
            systolic: Systolic pressure (mmHg)
            diastolic: Diastolic pressure (mmHg)
            pulse: Heart rate (bpm), optional
            measurement_timestamp_local: ISO 8601 timestamp, defaults to now
            client: Optional HTTP client (uses default if not provided)

        Returns:
            BloodPressure instance with updated data or None if 204 response
        """
        client = client or http.client
        path = "/bloodpressure-service/bloodpressure"

        payload: dict[str, int | str] = {
            "systolic": systolic,
            "diastolic": diastolic,
        }
        if pulse is not None:
            payload["pulse"] = pulse
        if measurement_timestamp_local is not None:
            payload["measurementTimestampLocal"] = measurement_timestamp_local

        result = client.connectapi(path, method="POST", json=payload)

        if not result:
            return None

        assert isinstance(result, dict), (
            f"Expected dict from {path}, got {type(result).__name__}"
        )
        result = camel_to_snake_dict(result)

        # Convert blood_pressure_measurements to BloodPressureReading objects
        if result.get("blood_pressure_measurements"):
            measurements = []
            for m in result["blood_pressure_measurements"]:
                measurements.append(
                    BloodPressureReading(**camel_to_snake_dict(m))
                )
            result["blood_pressure_measurements"] = measurements

        return cls(**result)

    @staticmethod
    def categories(
        *, client: http.Client | None = None
    ) -> list[BloodPressureCategory]:
        """Get blood pressure measurement categories.

        Args:
            client: Optional HTTP client (uses default if not provided)

        Returns:
            List of BloodPressureCategory instances
        """
        client = client or http.client
        path = "/bloodpressure-service/bloodpressure/category/level"

        data = client.connectapi(path)
        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )

        categories = []
        data = camel_to_snake_dict(data)

        # Extract all measurement categories from country entries
        for country_entry in data.get("country_measurement_categories", []):
            for cat in country_entry.get("measurement_categories", []):
                categories.append(
                    BloodPressureCategory(**camel_to_snake_dict(cat))
                )

        # Also add default measurement categories
        for cat in data.get("default_measurement_categories", []):
            categories.append(
                BloodPressureCategory(**camel_to_snake_dict(cat))
            )

        return categories


@dataclass
class BloodPressureRange:
    """Blood pressure range (min/max values)."""

    min: int
    max: int


@dataclass
class BloodPressureCategory:
    """Blood pressure measurement category/classification."""

    category: str
    systolic: BloodPressureRange
    diastolic: BloodPressureRange
