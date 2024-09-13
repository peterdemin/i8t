import json
import logging
import time
from functools import wraps

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


class IntrospectDecorator:
    instance = None

    def __init__(self, client: IntrospectClient) -> None:
        self._client = client

    def register(self) -> None:
        self.__class__.instance = self

    def unregister(self) -> None:
        self.__class__.instance = None

    def wrapper(self, func, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-except
            self._client.send(
                self._client.make_checkpoint(
                    func.__name__,
                    {"args": args, "kwargs": kwargs},
                    {"error": str(exc)},
                    start_time,
                )
            )
            raise
        self._client.send(
            self._client.make_checkpoint(
                func.__name__,
                {"args": args, "kwargs": kwargs},
                result,
                start_time,
            )
        )
        return result


def introspect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if IntrospectDecorator.instance:
            return IntrospectDecorator.instance.wrapper(func, *args, **kwargs)
        return func(*args, **kwargs)

    return wrapper
