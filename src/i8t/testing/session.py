import json
from typing import Callable, List


class IntrospectSession:
    def __init__(self, records: List[dict]) -> None:
        self._records = records

    @classmethod
    def from_jsonl(cls, jsonl: str, main_is: str = "") -> "IntrospectSession":
        with open(jsonl, encoding="utf-8") as fobj:
            records = [json.loads(line.strip()) for line in fobj]
            for record in records:
                record["location"] = record["location"].replace("__main__", main_is)
            return cls(records)

    def filter_by(self, filter_func: Callable[[dict], bool]) -> List[dict]:
        return [record for record in self._records if filter_func(record)]
