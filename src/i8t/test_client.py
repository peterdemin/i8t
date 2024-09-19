import logging
import unittest
from unittest import mock

import requests

from .client import IntrospectClient, logger


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
