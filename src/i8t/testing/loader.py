import contextlib
import fnmatch
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Tuple
from urllib.parse import urlparse

import requests_mock


@dataclass
class TestCase:
    args: List[Any]
    kwargs: Dict[str, Any]
    expected: Any

    @classmethod
    def from_record(cls, record: dict) -> "TestCase":
        return TestCase(
            args=record["input"]["args"],
            kwargs=record["input"]["kwargs"],
            expected=record["output"],
        )


@dataclass
class HTTPCall:  # pylint: disable=too-many-instance-attributes
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
    def from_record(cls, record: dict) -> "HTTPCall":
        return cls(
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


def load_session(jsonl: str) -> List[dict]:
    with open(jsonl, encoding="utf-8") as fobj:
        return [json.loads(line.strip()) for line in fobj]


def filter_by_location(location: str, records: List[dict]) -> List[dict]:
    return [record for record in records if record["location"].partition("/")[2] == location]


def filter_by_url_path(path: str, records: List[dict]) -> List[dict]:
    return [record for record in records if match_path(path, record["input"]["url"])]


def match_path(path: str, url: str) -> bool:
    return fnmatch.fnmatch(urlparse(url).path, path)


def load_test_cases(jsonl: str, location: str) -> Tuple[str, List[TestCase]]:
    return "case", [
        TestCase.from_record(record) for record in filter_by_location(location, load_session(jsonl))
    ]


def load_flask_calls(jsonl: str, path: str) -> Tuple[str, List[HTTPCall]]:
    return "case", [
        HTTPCall.from_record(record)
        for record in filter_by_url_path(path, filter_by_location("flask", load_session(jsonl)))
    ]


@contextlib.contextmanager
def load_request_mocks(jsonl: str) -> Iterator:
    with requests_mock.Mocker() as mocker:
        for record in filter_by_location("requests", load_session(jsonl)):
            mocker.register_uri(
                record["input"]["method"],
                record["input"]["url"],
                text=record["output"]["body"],
                headers=record["output"]["headers"],
                status_code=record["output"]["status_code"],
            )
        yield
