import json
from typing import List, TextIO

from .storage import IntrospectStorage


class IntrospectInMemoryStorage(IntrospectStorage):
    def __init__(self) -> None:
        self.checkpoints: List[dict] = []

    def save(self, checkpoint: dict) -> None:
        self.checkpoints.append(checkpoint)

    def dump(self, fobj: TextIO) -> None:
        for checkpoint in self.checkpoints:
            json.dump(checkpoint, fobj)
            fobj.write("\n")
