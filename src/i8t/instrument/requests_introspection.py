import time

import requests

from ..client import IntrospectionClient


class RequestsIntrospection:
    def __init__(self, client: IntrospectionClient) -> None:
        self._client = client
        self._original_request = requests.Session.request
        self._session = requests.Session()
        self._session_request = self._session.request

    def register(self) -> None:
        requests.Session.request = self._instrumented_request  # type: ignore[assignment]

    def unregister(self) -> None:
        requests.Session.request = self._original_request  # type: ignore[assignment]

    def _instrumented_request(self, method, url, **kwargs):
        if url == self._client.api_url:
            return self._session_request(method, url, **kwargs)
        start_time = time.time()
        try:
            response = self._session_request(method, url, **kwargs)
        except Exception as exc:
            self._client.send(
                self._client.make_checkpoint(
                    "requests",
                    {
                        "method": method,
                        "url": url,
                        "headers": dict(kwargs.get("headers", {})),
                        "body": kwargs.get("data", None),
                    },
                    {"error": str(exc)},
                    time.time() - start_time,
                )
            )
            raise
        self._client.send(
            self._client.make_checkpoint(
                "requests",
                {
                    "method": method,
                    "url": url,
                    "headers": dict(kwargs.get("headers", {})),
                    "body": kwargs.get("data", None),
                },
                {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                },
                time.time() - start_time,
            )
        )
        return response
