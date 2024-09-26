import base64
import json
from typing import Any, Tuple

import dill  # type: ignore


class DecoratorSerde:
    def serialize(self, location, input_, output, start_time) -> dict:
        input_hint, input_str = self._encode(input_)
        output_hint, output_str = self._encode(output)
        return dict(
            location=location,
            input_data=input_str,
            output_data=output_str,
            start_ts=start_time,
            input_hint=input_hint,
            output_hint=output_hint,
        )

    def deserialize(self, checkpoint: dict) -> dict:
        return dict(
            checkpoint,
            input=self._decode(checkpoint["input"], checkpoint["metadata"].get("input_hint", "")),
            output=self._decode(
                checkpoint["output"], checkpoint["metadata"].get("output_hint", "")
            ),
        )

    def _decode(self, obj_str: str, hint: str) -> Any:
        return (
            json.loads(obj_str)
            if hint == "json"
            else dill.loads(base64.b85decode(obj_str.encode("utf-8")))
        )

    def _encode(self, obj) -> Tuple[str, str]:
        try:
            return "json", json.dumps(obj)
        except TypeError:
            return "dill", base64.b85encode(dill.dumps(obj, recurse=True)).decode("utf-8")
