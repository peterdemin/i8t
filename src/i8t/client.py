import json
import logging
import time

import requests

logger = logging.getLogger(__name__)


class IntrospectClient:
    def __init__(self, session: requests.Session, api_url: str, name: str) -> None:
        self.api_url = api_url
        self._session = session
        self._name = name

    def send(self, data: dict) -> None:
        try:
            response = self._session.post(self.api_url, json=data)
            if response.status_code != 200:
                logger.error("Failed to send checkpoint: %r", response.text)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error sending checkpoint")

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
