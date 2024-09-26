import contextvars
import logging
import time
import uuid
from typing import Optional

import requests

from .relay_storage import RelayStorage
from .storage import IntrospectStorage

logger = logging.getLogger(__name__)
_INTROSPECT_CONTEXT: contextvars.ContextVar[str] = contextvars.ContextVar(
    "_INTROSPECT_CONTEXT", default=""
)


class IntrospectClient:
    def __init__(
        self, api_url: str, name: str, storage: Optional[IntrospectStorage] = None
    ) -> None:
        self.api_url = api_url
        self._name = name
        self._storage = storage or RelayStorage(requests.Session(), api_url)

    def start_context(self, value: str = "") -> None:
        _INTROSPECT_CONTEXT.set(value or self._gen_random_context_value())

    def reset_context(self) -> None:
        _INTROSPECT_CONTEXT.set("")

    def send(self, data: dict) -> None:
        self._storage.save(data)

    def make_checkpoint(
        self, location: str, input_data: dict, output_data: dict, start_ts: float, **metadata
    ) -> dict:
        return {
            "metadata": dict(
                name=self._name,
                location=location,
                start_ts=start_ts,
                finish_ts=time.time(),
                context=_INTROSPECT_CONTEXT.get(""),
                **metadata,
            ),
            "input": input_data,
            "output": output_data,
        }

    def _gen_random_context_value(self) -> str:
        return uuid.uuid4().hex
