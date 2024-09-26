import unittest
from unittest import mock

from i8t.client import IntrospectClient
from i8t.inmemory_storage import IntrospectInMemoryStorage

from .decorator_introspect import DecoratorIntrospect, introspect


class TestDecoratorIntrospect(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = IntrospectInMemoryStorage()
        self.decorator = DecoratorIntrospect(
            IntrospectClient("http://example.com", "test_client", storage=self.storage)
        )
        self.decorator.register()

    def tearDown(self) -> None:
        self.decorator.unregister()

    def test_function_introspected(self):
        with mock.patch("time.time", side_effect=[1000, 2000]):
            result = dummy_func(1, 2)

        self.assertEqual(result, 3)
        assert self.storage.checkpoints == [
            {
                "metadata": {
                    "name": "test_client",
                    "location": "i8t.instrument.test_decorator_introspect.dummy_func",
                    "start_ts": 1000,
                    "finish_ts": 2000,
                    "context": "",
                    "input_hint": "json",
                    "output_hint": "json",
                },
                "input": '{"args": [1, 2], "kwargs": {}}',
                "output": "3",
            },
        ]

    def test_method_introspected(self):
        dummy = Dummy()
        with mock.patch("time.time", side_effect=[1000, 2000]):
            result = dummy.method(3)

        self.assertEqual(result, 6)
        assert self.storage.checkpoints == [
            {
                "metadata": {
                    "name": "test_client",
                    "location": "i8t.instrument.test_decorator_introspect.Dummy.method",
                    "start_ts": 1000,
                    "finish_ts": 2000,
                    "context": "",
                    "input_hint": "json",
                    "output_hint": "json",
                },
                "input": '{"args": [3], "kwargs": {}}',
                "output": "6",
            },
        ]

    def test_non_json_method_introspected(self):
        dummy = Dummy()
        with mock.patch("time.time", side_effect=[1, 2, 3, 4]):
            result = dummy.non_json(dummy, 3)

        self.assertEqual(result, 6)
        assert self.storage.checkpoints == [
            {
                "input": '{"args": [3], "kwargs": {}}',
                "metadata": {
                    "context": "",
                    "finish_ts": 3,
                    "input_hint": "json",
                    "location": "i8t.instrument.test_decorator_introspect.Dummy.method",
                    "name": "test_client",
                    "output_hint": "json",
                    "start_ts": 2,
                },
                "output": "6",
            },
            {
                "input": (
                    "fCQCO000000001elqie@VRC14l#D28ICL&)ZgX^Ub!}yCbS`vdb97&1Wn*u0VRUbDUukZ1a"
                    "&L2RWn*-dj0Hq>ZEbm!lawieluHAKl#B*zcVTj8bCi9QbuI"
                ),
                "metadata": {
                    "context": "",
                    "finish_ts": 4,
                    "input_hint": "dill",
                    "location": "i8t.instrument.test_decorator_introspect.Dummy.non_json",
                    "name": "test_client",
                    "output_hint": "json",
                    "start_ts": 1,
                },
                "output": "6",
            },
        ]

    def test_nested_function_introspected(self):
        dummy = Dummy()
        with mock.patch("time.time", side_effect=[1, 2, 3, 4]):
            result = dummy.nested(3)

        self.assertEqual(result, 12)
        assert self.storage.checkpoints == [
            {
                "metadata": {
                    "name": "test_client",
                    "location": "i8t.instrument.test_decorator_introspect.Dummy.nested.<locals>.func",
                    "start_ts": 2,
                    "finish_ts": 3,
                    "context": "",
                    "input_hint": "json",
                    "output_hint": "json",
                },
                "input": '{"args": [3, 6], "kwargs": {}}',
                "output": "9",
            },
            {
                "metadata": {
                    "name": "test_client",
                    "location": "i8t.instrument.test_decorator_introspect.Dummy.nested",
                    "start_ts": 1,
                    "finish_ts": 4,
                    "context": "",
                    "input_hint": "json",
                    "output_hint": "json",
                },
                "input": '{"args": [3], "kwargs": {}}',
                "output": "12",
            },
        ]

    def test_unregister_disables(self):
        # Disable introspect decorator and check that checkpoint is not sent
        self.decorator.unregister()
        self.assertEqual(dummy_func(1, 2), 3)
        assert not self.storage.checkpoints

    def test_exception_introspected(self):
        # Act & Assert
        with mock.patch("time.time", side_effect=[1000, 2000]):
            with self.assertRaises(ValueError):
                dummy_raise(1, 2)

        assert self.storage.checkpoints == [
            {
                "metadata": {
                    "name": "test_client",
                    "location": "i8t.instrument.test_decorator_introspect.dummy_raise",
                    "start_ts": 1000,
                    "finish_ts": 2000,
                    "context": "",
                    "input_hint": "json",
                    "output_hint": "json",
                },
                "input": '{"args": [1, 2], "kwargs": {}}',
                "output": '{"error": "Test exception"}',
            },
        ]


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

    @introspect
    def non_json(self, dummy: "Dummy", param: int) -> int:
        return dummy.method(param)
