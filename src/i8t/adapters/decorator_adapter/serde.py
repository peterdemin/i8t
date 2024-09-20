import base64
from typing import Any, Tuple

import dill  # type: ignore


class DecoratorSerde:
    def serialize(self, location, input_, output, start_time) -> Tuple:
        return (
            location,
            self._encode(input_),
            self._encode(output),
            start_time,
        )

    def deserialize(self, record: dict) -> dict:
        return dict(
            record,
            input=self._decode(record["input"]),
            output=self._decode(record["output"]),
        )

    def _decode(self, obj_str) -> Any:
        return dill.loads(base64.b85decode(obj_str.encode("utf-8")))

    def _encode(self, obj) -> str:
        return base64.b85encode(dill.dumps(obj, recurse=True)).decode("utf-8")
