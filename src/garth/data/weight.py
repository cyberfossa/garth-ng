import builtins
from datetime import date, datetime, timedelta, timezone
from itertools import chain

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .. import http
from ..utils import (
    camel_to_snake_dict,
    format_end_date,
    get_localized_datetime,
)
from ._base import MAX_WORKERS, Data


@dataclass(config=ConfigDict(extra="ignore"))
class WeightData(Data):
    weight: int
    timestamp_local: int = Field(alias="date")
    sample_pk: int | None = None
    calendar_date: date | None = None
    source_type: str | None = None
    timestamp_gmt: int | None = None
    weight_delta: float | None = None
    bmi: float | None = None
    body_fat: float | None = None
    body_water: float | None = None
    bone_mass: int | None = None
    muscle_mass: int | None = None
    physique_rating: float | None = None
    visceral_fat: float | None = None
    metabolic_age: int | None = None

    @property
    def datetime_utc(self) -> datetime:
        ts = (
            self.timestamp_gmt
            if self.timestamp_gmt is not None
            else self.timestamp_local
        )
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)

    @property
    def datetime_local(self) -> datetime:
        ts = (
            self.timestamp_gmt
            if self.timestamp_gmt is not None
            else self.timestamp_local
        )
        return get_localized_datetime(ts, self.timestamp_local)

    @classmethod
    def get(
        cls,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> Self | None:
        client = client or http.client
        day = format_end_date(day)
        path = f"/weight-service/weight/dayview/{day}"
        data = client.connectapi(path)
        assert isinstance(data, dict), (
            f"Expected dict from {path}, got {type(data).__name__}"
        )
        day_weight_list = data["dateWeightList"] if data else []

        if not day_weight_list:
            return None

        return cls(**camel_to_snake_dict(day_weight_list[0]))

    @classmethod
    def list(
        cls,
        end: date | str | None = None,
        days: int = 1,
        *,
        client: http.Client | None = None,
        max_workers: int = MAX_WORKERS,
    ) -> builtins.list[Self]:
        client = client or http.client
        end = format_end_date(end)
        start = end - timedelta(days=days - 1)

        data = client.connectapi(
            f"/weight-service/weight/range/{start}/{end}?includeAll=true"
        )
        assert isinstance(data, dict), (
            f"Expected dict from weight range API, got {type(data).__name__}"
        )
        weight_summaries = data["dailyWeightSummaries"] if data else []
        weight_metrics = chain.from_iterable(
            summary["allWeightMetrics"] for summary in weight_summaries
        )
        weight_data_list = (
            cls(**camel_to_snake_dict(weight_data))
            for weight_data in weight_metrics
        )
        return sorted(weight_data_list, key=lambda d: d.datetime_utc)

    @classmethod
    def create(
        cls,
        weight: float,
        *,
        timestamp: datetime | None = None,
        client: http.Client | None = None,
    ) -> None:
        """Create a weight measurement.

        Args:
            weight: Weight in kilograms (e.g. 72.5).
            timestamp: When the measurement was taken.
                Defaults to current local time when None.
            client: HTTP client instance.
        """
        client = client or http.client
        if timestamp is None:
            dt = datetime.now().astimezone()
        else:
            dt = timestamp if timestamp.tzinfo else timestamp.astimezone()
        dt_gmt = dt.astimezone(timezone.utc)
        path = "/weight-service/user-weight"
        client.connectapi(
            path,
            method="POST",
            json={
                "dateTimestamp": dt.isoformat()[:19] + ".00",
                "gmtTimestamp": dt_gmt.isoformat()[:19] + ".00",
                "unitKey": "kg",
                "value": weight,
            },
        )

    @classmethod
    def delete(
        cls,
        sample_pk: int,
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> None:
        """Delete a weight measurement.

        Args:
            sample_pk: The unique identifier of the weight record.
            day: Date of the measurement in YYYY-MM-DD format.
                Defaults to today when None.
            client: HTTP client instance.
        """
        client = client or http.client
        day = format_end_date(day)
        path = f"/weight-service/weight/{day}/byversion/{sample_pk}"
        client.connectapi(path, method="DELETE")
