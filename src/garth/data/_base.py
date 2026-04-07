import builtins
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from itertools import chain
from typing import TypeVar

from .. import http
from ..utils import date_range, format_end_date


MAX_WORKERS = 10
_DataT = TypeVar("_DataT", bound="Data")


class Data(ABC):
    @classmethod
    @abstractmethod
    def get(
        cls: type[_DataT],
        day: date | str | None = None,
        *,
        client: http.Client | None = None,
    ) -> _DataT | builtins.list[_DataT] | None: ...

    @classmethod
    def list(
        cls: type[_DataT],
        end: date | str | None = None,
        days: int = 1,
        *,
        client: http.Client | None = None,
        max_workers: int = MAX_WORKERS,
    ) -> builtins.list[_DataT]:
        client = client or http.client
        end = format_end_date(end)

        def fetch_date(date_):
            if day := cls.get(date_, client=client):
                return day

        dates = date_range(end, days)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            data = list(executor.map(fetch_date, dates))
            data = [day for day in data if day is not None]

        return list(
            chain.from_iterable(
                day if isinstance(day, list) else [day] for day in data
            )
        )
