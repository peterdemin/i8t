import json
import logging

import requests

from .storage import IntrospectStorage

logger = logging.getLogger(__name__)


class RelayStorage(IntrospectStorage):
    def __init__(self, session: requests.Session, api_url: str) -> None:
        self._api_url = api_url
        self._session = session
        self._relay_converter = RelayConverter()

    def save(self, checkpoint: dict) -> None:
        try:
            response = self._session.post(
                self._api_url, json=self._relay_converter.to_relay(checkpoint)
            )
            if response.status_code != 200:
                logger.error("Failed to send checkpoint: %r", response.text)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error sending checkpoint")


class RelayConverter:
    @staticmethod
    def from_relay(checkpoint: dict) -> dict:
        return dict(
            checkpoint,
            input=json.loads(checkpoint["input"]),
            output=json.loads(checkpoint["output"]),
        )

    @staticmethod
    def to_relay(checkpoint: dict) -> dict:
        return dict(
            checkpoint,
            input=json.dumps(checkpoint["input"]),
            output=json.dumps(checkpoint["output"]),
        )
