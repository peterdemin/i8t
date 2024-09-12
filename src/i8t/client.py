import json
import logging
import time
from functools import wraps

import requests

logger = logging.getLogger(__name__)


class IntrospectionClient:
    def __init__(self, session: requests.Session, api_url: str, name: str) -> None:
        self.api_url = api_url
        self._session = session
        self._name = name

    def send(self, data):
        try:
            response = self._session.post(self.api_url, json=data)
            if response.status_code != 200:
                logger.error("Failed to send checkpoint: %r", response.text)
        except Exception as e:
            logger.exception("Error sending checkpoint")

    def make_checkpoint(
        self, location: str, input_data: dict, output_data: dict, duration: float
    ) -> None:
        return {
            "location": f"{self._name}/{location}",
            "timestamp": time.time(),
            "input": json.dumps(input_data),
            "output": json.dumps(output_data),
            "metadata": {"duration": duration},
        }


class IntrospectionDecorator:
    instance = None

    def __init__(self, client: IntrospectionClient) -> None:
        self._client = client

    def register(self) -> None:
        self.__class__.instance = self

    def wrapper(self, func, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            self._client.send(
                self._client.make_checkpoint(
                    func.__name__,
                    {"args": args, "kwargs": kwargs},
                    {"error": str(e)},
                    time.time() - start_time,
                )
            )
            raise
        self._client.send(
            self._client.make_checkpoint(
                func.__name__,
                {"args": args, "kwargs": kwargs},
                result,
                time.time() - start_time,
            )
        )
        return result


def introspect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if IntrospectionDecorator.instance:
            return IntrospectionDecorator.instance.wrapper(func, *args, **kwargs)
        return func(*args, **kwargs)

    return wrapper
