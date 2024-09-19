import contextlib
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, Tuple

import requests

from i8t.client import IntrospectClient


@dataclass
class _Params:
    start_time: float
    method: str
    url: str
    kwargs: Dict[str, Any]


class RequestsAdapter:
    LOCATION = "requests"

    def __init__(self, client: IntrospectClient) -> None:
        self._client = client

    def should_record(self, url: str) -> bool:
        return url != self._client.api_url

    @contextlib.contextmanager
    def record(
        self, method: str, url: str, kwargs: Dict[str, Any]
    ) -> Iterator[Callable[[requests.Response], requests.Response]]:
        params = _Params(start_time=time.time(), method=method, url=url, kwargs=kwargs)

        def recorder(response: requests.Response) -> requests.Response:
            self._send(self._for_success(params, response))
            return response

        try:
            yield recorder
        except Exception as exc:
            self._send(self._for_exception(params, exc))
            raise

    def _send(self, checkpoint_params: Tuple) -> None:
        self._client.send(self._client.make_checkpoint(*checkpoint_params))

    def _for_success(self, params: _Params, response: requests.Response) -> Tuple:
        return (
            self.LOCATION,
            self._input(params),
            {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
            },
            params.start_time,
        )

    def _for_exception(self, params: _Params, exc: Exception) -> Tuple:
        return (
            self.LOCATION,
            self._input(params),
            {"error": str(exc)},
            params.start_time,
        )

    def _input(self, params: _Params) -> dict:
        return {
            "method": params.method,
            "url": params.url,
            "headers": dict(params.kwargs.get("headers", {})),
            "body": params.kwargs.get("data", None),
        }
