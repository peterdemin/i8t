import requests

from i8t.adapters.requests_adapter.exporter import RequestsAdapter
from i8t.client import IntrospectClient


class RequestsIntrospect:
    def __init__(self, client: IntrospectClient) -> None:
        self._client = client
        self._original_request = requests.Session.request
        self._session_request = requests.Session().request
        self._requests_adapter = RequestsAdapter(self._client)

    def register(self) -> None:
        requests.Session.request = self._instrumented_request  # type: ignore[assignment]

    def unregister(self) -> None:
        requests.Session.request = self._original_request  # type: ignore[assignment]

    def _instrumented_request(self, method, url, **kwargs):
        if not self._requests_adapter.should_record(url):
            return self._session_request(method, url, **kwargs)
        with self._requests_adapter.record(method, url, kwargs) as recorder:
            return recorder(self._session_request(method, url, **kwargs))
