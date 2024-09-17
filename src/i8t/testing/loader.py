import contextlib
import fnmatch
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple
from unittest import mock
from urllib.parse import urlparse

import requests_mock


@dataclass
class TimeRange:
    start_ts: float
    finish_ts: float


@dataclass
class Checkpoint(TimeRange):
    args: List[Any]
    kwargs: Dict[str, Any]
    expected: Any
    qualname: str

    @classmethod
    def from_record(cls, record: dict) -> "Checkpoint":
        return cls(
            start_ts=record["start_ts"],
            finish_ts=record["finish_ts"],
            args=record["input"]["args"],
            kwargs=record["input"]["kwargs"],
            expected=record["output"],
            qualname=record["location"].partition("/")[2],
        )


@dataclass
class HTTPCall(TimeRange):  # pylint: disable=too-many-instance-attributes
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


def load_session(jsonl: str) -> List[dict]:
    with open(jsonl, encoding="utf-8") as fobj:
        return [json.loads(line.strip()) for line in fobj]


def filter_by_location(location: str, records: List[dict]) -> List[dict]:
    return [
        record
        for record in records
        if fnmatch.fnmatch(record["location"].partition("/")[2], "*" + location)
    ]


def filter_by_url_path(path: str, records: List[dict]) -> List[dict]:
    return [record for record in records if match_path(path, record["input"]["url"])]


def filter_within_time_range(within: Optional[TimeRange], records: List[dict]) -> List[dict]:
    if not within:
        return records
    return [
        record
        for record in records
        if record["start_ts"] >= within.start_ts and record["finish_ts"] <= within.finish_ts
    ]


def match_path(path: str, url: str) -> bool:
    return fnmatch.fnmatch(urlparse(url).path, path)


def load_test_cases(jsonl: str, location: str) -> Tuple[str, List[Checkpoint]]:
    return "case", [
        Checkpoint.from_record(record)
        for record in filter_by_location(location, load_session(jsonl))
    ]


def load_flask_calls(jsonl: str, path: str) -> Tuple[str, List[HTTPCall]]:
    return "case", [
        HTTPCall.from_record(record)
        for record in filter_by_url_path(path, filter_by_location("flask", load_session(jsonl)))
    ]


@contextlib.contextmanager
def load_requests_mocks(jsonl: str, within: Optional[TimeRange] = None) -> Iterator:
    records = filter_within_time_range(within, filter_by_location("requests", load_session(jsonl)))
    with requests_mock.Mocker() as mocker:
        for record in records:
            mocker.register_uri(
                record["input"]["method"],
                record["input"]["url"],
                text=record["output"]["body"],
                headers=record["output"]["headers"],
                status_code=record["output"]["status_code"],
            )
        yield


@dataclass
class Patch:
    name: str
    checkpoints: List[Checkpoint]


@dataclass
class CheckpointMock:
    name: str
    checkpoints: List[Checkpoint]
    mock_obj: mock.Mock
    call_args_list: List[Any]


@contextlib.contextmanager
def patch_checkpoints(jsonl: str, name: str = "", within: Optional[TimeRange] = None) -> Iterator:
    records = filter_within_time_range(within, filter_by_location(name, load_session(jsonl)))
    if not records:
        yield []
        return
    by_name: Dict[str, List[Checkpoint]] = {}
    for record in records:
        checkpoint = Checkpoint.from_record(record)
        by_name.setdefault(checkpoint.qualname, []).append(checkpoint)
    patches = [Patch(name=name, checkpoints=checkpoints) for name, checkpoints in by_name.items()]
    with patch_many(patches) as expected_calls:
        yield expected_calls


@contextlib.contextmanager
def patch_many(patches: List[Patch]) -> Iterator:
    patch = patches[0]
    side_effect = [checkpoint.expected for checkpoint in patch.checkpoints]
    with mock.patch(patch.name, autospec=True, side_effect=side_effect) as mocked:
        checkpoint_mock = CheckpointMock(
            name=patch.name,
            checkpoints=patch.checkpoints,
            mock_obj=mocked,
            call_args_list=[
                mock.call(*checkpoint.args, **checkpoint.kwargs) for checkpoint in patch.checkpoints
            ],
        )
        if patches[1:]:
            with patch_many(patches[1:]) as expected_calls:
                yield [checkpoint_mock] + expected_calls
        else:
            yield [checkpoint_mock]
        # assert mocked.call_args_list == [
        #     mock.call(*checkpoint.args, **checkpoint.kwargs) for checkpoint in patch.checkpoints
        # ]
