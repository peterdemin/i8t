import logging
import unittest
from unittest import mock

import requests

from .client import IntrospectClient, IntrospectDecorator, introspect, logger


class TestIntrospectClient(unittest.TestCase):
    def setUp(self) -> None:
        logger.setLevel(logging.ERROR)
        logger.addHandler(logging.StreamHandler())

    def test_send_successful(self):
        # Arrange
        mock_session = mock.Mock(requests.Session)
        mock_session.post.return_value.status_code = 200
        client = IntrospectClient(mock_session, "http://example.com", "test_client")

        # Act
        client.send({"key": "value"})

        # Assert
        mock_session.post.assert_called_once_with("http://example.com", json={"key": "value"})

    def test_send_failure(self):
        # Arrange
        mock_session = mock.Mock(requests.Session)
        mock_session.post.return_value.status_code = 500
        client = IntrospectClient(mock_session, "http://example.com", "test_client")

        # Act
        with self.assertLogs(logger=logger, level="DEBUG") as log:
            client.send({"key": "value"})

        # Assert
        self.assertIn("ERROR:i8t.client:Failed to send checkpoint", log.output[0])

    def test_send_exception(self):
        # Arrange
        mock_session = mock.Mock(requests.Session)
        mock_session.post.side_effect = Exception("Test exception")
        client = IntrospectClient(mock_session, "http://example.com", "test_client")

        # Act
        with self.assertLogs(logger=logger, level="ERROR") as log:
            client.send({"key": "value"})

        # Assert
        self.assertIn("ERROR:i8t.client:Error sending checkpoint", log.output[0])

    @mock.patch("time.time", return_value=5)
    def test_make_checkpoint(self, _):
        # Arrange
        client = IntrospectClient(None, "http://example.com", "test_client")

        # Act
        checkpoint = client.make_checkpoint("location1", {"input": "data"}, {"output": "data"}, 1)

        # Assert
        expected_checkpoint = {
            "location": "test_client/location1",
            "start_ts": 1,
            "finish_ts": 5,
            "input": '{"input": "data"}',
            "output": '{"output": "data"}',
        }
        self.assertEqual(checkpoint, expected_checkpoint)


class TestIntrospectDecorator(unittest.TestCase):
    @mock.patch("time.time", side_effect=[1000, 2000])
    def test_wrapper_success(self, _):
        # Arrange
        mock_client = mock.Mock(IntrospectClient)
        decorator = IntrospectDecorator(mock_client)
        decorator.register()

        @introspect
        def test_func(first, second):
            return first + second

        # Act
        result = test_func(1, 2)

        # Assert
        self.assertEqual(result, 3)
        mock_client.send.assert_called_once()

        # Arrange
        decorator.unregister()

        # Act
        result = test_func(1, 2)

        # Assert
        self.assertEqual(result, 3)
        mock_client.send.assert_called_once()

    @mock.patch("time.time", side_effect=[1000, 2000])
    def test_wrapper_exception(self, _):
        # Arrange
        mock_client = mock.Mock(IntrospectClient)
        decorator = IntrospectDecorator(mock_client)
        decorator.register()

        @introspect
        def test_func(first, second):
            raise ValueError("Test exception")

        # Set up the return value for make_checkpoint mock
        mock_client.make_checkpoint.return_value = {
            "location": "test_func",
            "input": {"args": (1, 2), "kwargs": {}},
            "output": {"error": "Test exception"},
            "start_ts": 1000,
            "finish_ts": 2000,
        }

        # Act & Assert
        with self.assertRaises(ValueError):
            test_func(1, 2)

        mock_client.send.assert_called_once()
        send_call_args = mock_client.send.call_args[0][0]
        self.assertIn("error", send_call_args["output"])
