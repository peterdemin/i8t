import contextlib
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional

import requests_mock

from i8t.testing.session import IntrospectSession
from i8t.testing.time_range import TimeRange

from .exporter import RequestsAdapter


@dataclass
class RequestsMock:
    method: str
    url: str
    text: str
    headers: Dict[str, str]
    status_code: int

    @classmethod
    def from_record(cls, record: dict) -> "RequestsMock":
        return cls(
            method=record["input"]["method"],
            url=record["input"]["url"],
            text=record["output"]["body"],
            headers=record["output"]["headers"],
            status_code=record["output"]["status_code"],
        )

    def register(self, mocker: requests_mock.Mocker) -> None:
        mocker.register_uri(
            self.method,
            self.url,
            text=self.text,
            headers=self.headers,
            status_code=self.status_code,
        )

    @classmethod
    @contextlib.contextmanager
    def activate(cls, session: IntrospectSession, within: Optional[TimeRange] = None) -> Iterator:
        with requests_mock.Mocker() as mocker:
            for case in cls.load(session, within):
                case.register(mocker)
            yield

    @classmethod
    def load(cls, session: IntrospectSession, within: Optional[TimeRange]) -> List["RequestsMock"]:
        return [cls.from_record(record) for record in session.filter_by(RequestsFilter(within))]


class RequestsFilter:
    def __init__(self, within: Optional[TimeRange]) -> None:
        self._within = within

    def __call__(self, record: dict) -> bool:
        return self._match_location(record["location"]) and self._match_within(record)

    def _match_location(self, location: str) -> bool:
        return location.partition("/")[2] == RequestsAdapter.LOCATION

    def _match_within(self, record: dict) -> bool:
        if not self._within:
            return True
        return (
            record["start_ts"] >= self._within.start_ts
            and record["finish_ts"] <= self._within.finish_ts
        )
