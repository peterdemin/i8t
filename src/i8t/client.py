import logging
import time
from typing import Optional

import requests

from .relay_storage import RelayStorage
from .storage import IntrospectStorage

logger = logging.getLogger(__name__)


class IntrospectClient:
    def __init__(
        self, api_url: str, name: str, storage: Optional[IntrospectStorage] = None
    ) -> None:
        self.api_url = api_url
        self._name = name
        self._storage = storage or RelayStorage(requests.Session(), api_url)

    def send(self, data: dict) -> None:
        self._storage.save(data)

    def make_checkpoint(
        self, location: str, input_data: dict, output_data: dict, start_ts: float
    ) -> dict:
        return {
            "location": f"{self._name}/{location}",
            "start_ts": start_ts,
            "finish_ts": time.time(),
            "input": input_data,
            "output": output_data,
        }
