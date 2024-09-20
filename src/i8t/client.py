import json
import logging
import time
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


class IntrospectStorage:
    def save(self, data: dict) -> None:
        raise NotImplementedError()  # pragma: no cover


class IntrospectClient:
    def __init__(
        self, api_url: str, name: str, storage: Optional[IntrospectStorage] = None
    ) -> None:
        self.api_url = api_url
        self._name = name
        self._storage = storage or IntrospectRequestsStorage(requests.Session(), api_url)

    def send(self, data: dict) -> None:
        self._storage.save(data)

    def make_checkpoint(
        self, location: str, input_data: dict, output_data: dict, start_ts: float
    ) -> dict:
        return {
            "location": f"{self._name}/{location}",
            "start_ts": start_ts,
            "finish_ts": time.time(),
            "input": json.dumps(input_data),
            "output": json.dumps(output_data),
        }


class IntrospectRequestsStorage(IntrospectStorage):
    def __init__(self, session: requests.Session, api_url: str) -> None:
        self._api_url = api_url
        self._session = session

    def save(self, data: dict) -> None:
        try:
            response = self._session.post(self._api_url, json=data)
            if response.status_code != 200:
                logger.error("Failed to send checkpoint: %r", response.text)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error sending checkpoint")


class IntrospectInMemoryStorage(IntrospectStorage):
    def __init__(self) -> None:
        self.records: List[dict] = []

    def save(self, data: dict) -> None:
        self.records.append(data)
