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

    def test_make_checkpoint(self):
        # Arrange
        client = IntrospectClient(None, "http://example.com", "test_client")

        # Act
        with mock.patch("time.time", return_value=5):
            checkpoint = client.make_checkpoint(
                "location1", {"input": "data"}, {"output": "data"}, 1
            )

        # Assert
        self.assertEqual(
            checkpoint,
            {
                "location": "test_client/location1",
                "start_ts": 1,
                "finish_ts": 5,
                "input": '{"input": "data"}',
                "output": '{"output": "data"}',
            },
        )


class TestIntrospectDecorator(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_session = mock.Mock(requests.Session)
        self.mock_session.post.return_value.status_code = 200
        self.decorator = IntrospectDecorator(
            IntrospectClient(self.mock_session, "http://example.com", "test_client")
        )
        self.decorator.register()

    def tearDown(self) -> None:
        self.decorator.unregister()

    def test_function_introspected(self):
        with mock.patch("time.time", side_effect=[1000, 2000]):
            result = dummy_func(1, 2)

        self.assertEqual(result, 3)
        self.mock_session.post.assert_called_once_with(
            "http://example.com",
            json={
                "location": "test_client/i8t.test_client.dummy_func",
                "start_ts": 1000,
                "finish_ts": 2000,
                "input": '{"args": [1, 2], "kwargs": {}}',
                "output": "3",
            },
        )

    def test_method_introspected(self):
        dummy = Dummy()
        with mock.patch("time.time", side_effect=[1000, 2000]):
            result = dummy.method(3)

        self.assertEqual(result, 6)
        self.mock_session.post.assert_called_once_with(
            "http://example.com",
            json={
                "location": "test_client/i8t.test_client.Dummy.method",
                "start_ts": 1000,
                "finish_ts": 2000,
                "input": '{"args": [3], "kwargs": {}}',
                "output": "6",
            },
        )

    def test_nested_function_introspected(self):
        dummy = Dummy()
        with mock.patch("time.time", side_effect=[1, 2, 3, 4]):
            result = dummy.nested(3)

        self.assertEqual(result, 12)
        assert self.mock_session.post.call_args_list == [
            mock.call(
                "http://example.com",
                json={
                    "location": "test_client/i8t.test_client.Dummy.nested.<locals>.func",
                    "start_ts": 2,
                    "finish_ts": 3,
                    "input": '{"args": [3, 6], "kwargs": {}}',
                    "output": "9",
                },
            ),
            mock.call(
                "http://example.com",
                json={
                    "location": "test_client/i8t.test_client.Dummy.nested",
                    "start_ts": 1,
                    "finish_ts": 4,
                    "input": '{"args": [3], "kwargs": {}}',
                    "output": "12",
                },
            ),
        ]

    def test_unregister_disables(self):
        # Disable introspect decorator and check that checkpoint is not sent
        self.decorator.unregister()
        self.assertEqual(dummy_func(1, 2), 3)
        self.mock_session.post.assert_not_called()

    def test_exception_introspected(self):
        # Act & Assert
        with mock.patch("time.time", side_effect=[1000, 2000]):
            with self.assertRaises(ValueError):
                dummy_raise(1, 2)

        self.mock_session.post.assert_called_once_with(
            "http://example.com",
            json={
                "location": "test_client/i8t.test_client.dummy_raise",
                "start_ts": 1000,
                "finish_ts": 2000,
                "input": '{"args": [1, 2], "kwargs": {}}',
                "output": '{"error": "Test exception"}',
            },
        )


@introspect
def dummy_func(first, second):
    return first + second


@introspect
def dummy_raise(first, second):
    raise ValueError("Test exception")


class Dummy:
    @introspect
    def method(self, param: int) -> int:
        return param * 2

    @introspect
    def nested(self, param: int) -> int:
        @introspect
        def func(first, second):
            return first + second

        return func(param, param * 2) + param
