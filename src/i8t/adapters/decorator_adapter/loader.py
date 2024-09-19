import contextlib
import fnmatch
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional
from unittest import mock

from i8t.testing.session import IntrospectSession
from i8t.testing.time_range import TimeRange

from .serde import DecoratorSerde


@dataclass
class DecoratedCase(TimeRange):
    args: List[Any]
    kwargs: Dict[str, Any]
    expected: Any
    qualname: str
    _serde = DecoratorSerde()

    @classmethod
    def from_record(cls, raw_record: dict) -> "DecoratedCase":
        record = cls._serde.deserialize(raw_record)
        return cls(
            start_ts=record["start_ts"],
            finish_ts=record["finish_ts"],
            args=record["input"]["args"],
            kwargs=record["input"]["kwargs"],
            expected=record["output"],
            qualname=record["location"].partition("/")[2],
        )

    @classmethod
    def load(
        cls, session: IntrospectSession, name: str, within: Optional[TimeRange] = None
    ) -> List["DecoratedCase"]:
        return [
            cls.from_record(record) for record in session.filter_by(DecoratorFilter(name, within))
        ]


@dataclass
class Patch:
    qualname: str
    cases: List[DecoratedCase]


@dataclass
class DecoratedPatch:
    qualname: str
    cases: List[DecoratedCase]
    mock_obj: mock.Mock
    call_args_list: List[Any]

    @classmethod
    @contextlib.contextmanager
    def activate(
        cls,
        session: IntrospectSession,
        name: str = "",
        within: Optional[TimeRange] = None,
    ) -> Iterator:
        records = session.filter_by(DecoratorFilter(name, within))
        if not records:
            yield []
        else:
            with patch_many(cls._group_by_qualname(records)) as expected_calls:
                yield expected_calls

    @staticmethod
    def _group_by_qualname(records: List[dict]) -> List[Patch]:
        by_qualname: Dict[str, List[DecoratedCase]] = {}
        for record in records:
            case = DecoratedCase.from_record(record)
            by_qualname.setdefault(case.qualname, []).append(case)
        return [Patch(qualname=qualname, cases=cases) for qualname, cases in by_qualname.items()]


@contextlib.contextmanager
def patch_many(patches: List[Patch]) -> Iterator[List[DecoratedPatch]]:
    patch = patches[0]
    side_effect = [case.expected for case in patch.cases]
    with mock.patch(patch.qualname, spec=True, side_effect=side_effect) as mocked:
        case_mock = DecoratedPatch(
            qualname=patch.qualname,
            cases=patch.cases,
            mock_obj=mocked,
            call_args_list=[mock.call(*case.args, **case.kwargs) for case in patch.cases],
        )
        if patches[1:]:
            with patch_many(patches[1:]) as expected_calls:
                yield [case_mock] + expected_calls
        else:
            yield [case_mock]


class DecoratorFilter:
    def __init__(self, name: str, within: Optional[TimeRange]) -> None:
        self._name = name
        self._within = within

    def __call__(self, record: dict) -> bool:
        return self._match_location(record["location"]) and self._match_within(record)

    def _match_location(self, location: str) -> bool:
        return fnmatch.fnmatch(location.partition("/")[2], "*" + self._name)

    def _match_within(self, record: dict) -> bool:
        if not self._within:
            return True
        return (
            record["start_ts"] >= self._within.start_ts
            and record["finish_ts"] <= self._within.finish_ts
        )
