import logging
import unittest
from unittest import mock

import requests

from .client import IntrospectClient
from .relay_storage import RelayStorage, logger


class TestIntrospectClient(unittest.TestCase):
    API_URL = "http://example.com"
    CHECKPOINT = {"input": "input", "output": "output"}
    SENT_CHECKPOINT = {"input": '"input"', "output": '"output"'}

    def setUp(self) -> None:
        logger.setLevel(logging.ERROR)
        logger.addHandler(logging.StreamHandler())

    def test_send_successful(self):
        # Arrange
        mock_session = mock.Mock(requests.Session)
        mock_session.post.return_value.status_code = 200
        storage = RelayStorage(mock_session, self.API_URL)
        client = IntrospectClient("http://example.com", "test_client", storage=storage)

        # Act
        client.send(self.CHECKPOINT)

        # Assert
        mock_session.post.assert_called_once_with("http://example.com", json=self.SENT_CHECKPOINT)

    def test_send_failure(self):
        # Arrange
        mock_session = mock.Mock(requests.Session)
        mock_session.post.return_value.status_code = 500
        storage = RelayStorage(mock_session, self.API_URL)
        client = IntrospectClient("http://example.com", "test_client", storage=storage)

        # Act
        with self.assertLogs(logger=logger, level="DEBUG") as log:
            client.send(self.CHECKPOINT)

        # Assert
        self.assertIn("ERROR:i8t.relay_storage:Failed to send checkpoint", log.output[0])

    def test_send_exception(self):
        # Arrange
        mock_session = mock.Mock(requests.Session)
        mock_session.post.side_effect = Exception("Test exception")
        storage = RelayStorage(mock_session, self.API_URL)
        client = IntrospectClient("http://example.com", "test_client", storage=storage)

        # Act
        with self.assertLogs(logger=logger, level="ERROR") as log:
            client.send(self.CHECKPOINT)

        # Assert
        self.assertIn("ERROR:i8t.relay_storage:Error sending checkpoint", log.output[0])

    def test_make_checkpoint(self):
        # Arrange
        client = IntrospectClient("http://example.com", "test_client")

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
                "input": {"input": "data"},
                "output": {"output": "data"},
            },
        )
