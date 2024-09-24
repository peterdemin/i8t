import io
import unittest

from .inmemory_storage import IntrospectInMemoryStorage


class TestIntrospectInMemoryStorage(unittest.TestCase):
    def test_dump_sample(self):
        storage = IntrospectInMemoryStorage()
        storage.save(
            {
                "location": "test_client/location1",
                "start_ts": 1,
                "finish_ts": 5,
                "input": {"input": "data"},
                "output": {"output": "data"},
            }
        )
        buf = io.StringIO()
        storage.dump(buf)
        assert buf.getvalue() == (
            '{"location": "test_client/location1", "start_ts": 1, '
            '"finish_ts": 5, "input": {"input": "data"}, "output": '
            '{"output": "data"}}\n'
        )
