import json
import unittest
from unittest import mock
from unittest.mock import patch

import flask
import requests

from ..client import IntrospectClient
from .flask_introspect import FlaskIntrospect


class TestFlaskIntrospect(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)
        self.mock_session = mock.Mock(requests.Session)
        self.mock_client = mock.Mock(
            wraps=IntrospectClient(self.mock_session, "api_url", "test_client")
        )
        self.flask_introspect = FlaskIntrospect(self.mock_client)
        self.flask_introspect.register(self.app)

        # A simple route for testing
        @self.app.route("/test", methods=["POST"])
        def test_route():
            return "Test Response", 200

    @patch("time.time", side_effect=[1, 5, 30, 100])
    def test_before_and_after_request(self, _):
        # Use Flask's test client to simulate requests
        with self.app.test_client() as client:
            # Act: send a POST request to the /test route
            client.post("/test", data="Test Body", headers={"Test-Header": "HeaderValue"})

            # Assert: Check if the before_request correctly sets the start time
            self.assertEqual(flask.g.start_time, 1)

        # Assert: Check if the after_request triggers the introspect client
        self.mock_client.send.assert_called_once_with(
            {
                "location": "test_client/flask",
                "start_ts": 1,
                "finish_ts": 5,
                "input": json.dumps(
                    {
                        "method": "POST",
                        "url": "http://localhost/test",
                        "headers": {
                            "User-Agent": "Werkzeug/3.0.4",
                            "Host": "localhost",
                            "Content-Length": "9",
                            "Test-Header": "HeaderValue",
                        },
                        "args": {},
                        "form": {},
                        "json": None,
                        "data": "Test Body",
                    }
                ),
                "output": json.dumps(
                    {
                        "status_code": 200,
                        "headers": {
                            "Content-Type": "text/html; charset=utf-8",
                            "Content-Length": "13",
                        },
                        "body": "Test Response",
                    }
                ),
            }
        )

    @patch("time.time", side_effect=[1, 5, 30, 100])
    def test_before_request(self, _):
        with self.app.test_client() as client:
            client.get("/test")

            # Assert: start time is set in g before the request
            self.assertEqual(flask.g.start_time, 1)

    @patch("time.time", side_effect=[1, 5, 30, 100])
    def test_after_request(self, _):
        with self.app.test_client() as client:
            client.get("/test")

            # Assert: after_request sends data to the introspect client
            self.mock_client.send.assert_called_once_with(
                {
                    "location": "test_client/flask",
                    "start_ts": 1,
                    "finish_ts": 5,
                    "input": mock.ANY,
                    "output": mock.ANY,
                }
            )
