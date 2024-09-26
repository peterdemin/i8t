import unittest
from unittest import mock

import requests
import requests_mock

from i8t.relay_storage import RelayStorage

from ..client import IntrospectClient
from .requests_introspect import RequestsIntrospect


class RequestsIntrospectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_session = mock.Mock(requests.Session)
        self.introspect_client = mock.Mock(
            wraps=IntrospectClient(
                "http://api_url",
                "test",
                storage=RelayStorage(self.mock_session, "api_url"),
            ),
            api_url="http://api_url",
        )
        self.requests_introspect = RequestsIntrospect(self.introspect_client)
        self.requests_introspect.register()

    def tearDown(self) -> None:
        self.requests_introspect.unregister()

    @requests_mock.Mocker()
    def test_instrumented_request_sends_checkpoint_for_success(self, req_mock) -> None:
        req_mock.post("http://external-api", text="ok")
        got = requests.post("http://external-api", json={"key": "value"}, timeout=1)
        assert got.text == "ok"
        self.introspect_client.send.assert_called_once_with(
            {
                "metadata": {
                    "name": "test",
                    "location": "requests",
                    "start_ts": mock.ANY,
                    "finish_ts": mock.ANY,
                    "context": "",
                },
                "input": {
                    "method": "post",
                    "url": "http://external-api",
                    "headers": {},
                    "body": None,
                },
                "output": {"status_code": 200, "headers": {}, "body": "ok"},
            }
        )

    @requests_mock.Mocker()
    def test_instrumented_request_sends_checkpoint_for_error(self, req_mock) -> None:
        req_mock.post("http://external-api/fail", status_code=500)
        got = requests.post("http://external-api/fail", json={"key": "value"}, timeout=1)
        assert got.status_code == 500
        self.introspect_client.send.assert_called_once_with(
            {
                "metadata": {
                    "name": "test",
                    "location": "requests",
                    "start_ts": mock.ANY,
                    "finish_ts": mock.ANY,
                    "context": "",
                },
                "input": {
                    "method": "post",
                    "url": "http://external-api/fail",
                    "headers": {},
                    "body": None,
                },
                "output": {"status_code": 500, "headers": {}, "body": ""},
            }
        )

    @requests_mock.Mocker()
    def test_instrumented_request_sends_checkpoint_for_exception(self, req_mock) -> None:
        req_mock.post("http://external-api/fail", exc=requests.exceptions.ConnectTimeout)
        with self.assertRaises(requests.exceptions.ConnectTimeout):
            requests.post("http://external-api/fail", json={"key": "value"}, timeout=1)
        self.introspect_client.send.assert_called_once_with(
            {
                "metadata": {
                    "name": "test",
                    "location": "requests",
                    "start_ts": mock.ANY,
                    "finish_ts": mock.ANY,
                    "context": "",
                },
                "input": {
                    "method": "post",
                    "url": "http://external-api/fail",
                    "headers": {},
                    "body": None,
                },
                "output": {"error": ""},
            }
        )

    @requests_mock.Mocker()
    def test_instrumented_request_skips_i8t_url(self, req_mock) -> None:
        req_mock.post("http://api_url", text="no")
        got = requests.post("http://api_url", json={"key": "value"}, timeout=1)
        assert got.text == "no"
        self.introspect_client.send.assert_not_called()
