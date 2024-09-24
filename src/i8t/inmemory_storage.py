import json
from typing import List, TextIO

from .storage import IntrospectStorage


class IntrospectInMemoryStorage(IntrospectStorage):
    def __init__(self) -> None:
        self.records: List[dict] = []

    def save(self, data: dict) -> None:
        self.records.append(data)

    def dump(self, fobj: TextIO) -> None:
        for record in self.records:
            json.dump(record, fobj)
            fobj.write("\n")
