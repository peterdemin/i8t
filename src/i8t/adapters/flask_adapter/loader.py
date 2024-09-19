import fnmatch
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib.parse import urlparse

import flask.testing
import werkzeug.test

from i8t.testing.session import IntrospectSession
from i8t.testing.time_range import TimeRange

from .exporter import FlaskAdapter


@dataclass
class FlaskCase(TimeRange):  # pylint: disable=too-many-instance-attributes
    url: str
    method: str
    headers: Dict[str, str]
    data: str
    form: Dict[str, Any]
    json: Dict[str, Any]
    expected_status_code: int
    expected_headers: Dict[str, str]
    expected_body: str

    @classmethod
    def from_record(cls, record: dict) -> "FlaskCase":
        return cls(
            start_ts=record["start_ts"],
            finish_ts=record["finish_ts"],
            url=record["input"]["url"],
            method=record["input"]["method"],
            headers=record["input"]["headers"],
            form=record["input"]["form"],
            json=record["input"]["json"],
            data=record["input"]["data"],
            expected_status_code=record["output"]["status_code"],
            expected_headers=record["output"]["headers"],
            expected_body=record["output"]["body"],
        )

    def call(self, client: flask.testing.FlaskClient) -> werkzeug.test.TestResponse:
        return client.open(self.url, method=self.method, json=self.json, headers=self.headers)

    @classmethod
    def load(cls, session: IntrospectSession, path: str) -> List["FlaskCase"]:
        return [cls.from_record(record) for record in session.filter_by(FlaskFilter(path))]


class FlaskFilter:
    def __init__(self, path: str) -> None:
        self._path = path

    def __call__(self, record: dict) -> bool:
        return self._match_location(record["location"]) and self._match_path(record["input"]["url"])

    def _match_location(self, location: str) -> bool:
        return location.partition("/")[2] == FlaskAdapter.LOCATION

    def _match_path(self, url: str) -> bool:
        return fnmatch.fnmatch(urlparse(url).path, self._path)
