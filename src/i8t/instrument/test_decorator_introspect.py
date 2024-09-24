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
        assert self.storage.records == [
            {
                "location": "test_client/i8t.instrument.test_decorator_introspect.dummy_func",
                "start_ts": 1000,
                "finish_ts": 2000,
                "input": "fCQBt000000001elqie@VRC14luH3i0)~`~25Wa=a%XdteUx=B",
                "output": "fCNheE&",
            },
        ]

    def test_method_introspected(self):
        dummy = Dummy()
        with mock.patch("time.time", side_effect=[1000, 2000]):
            result = dummy.method(3)

        self.assertEqual(result, 6)
        assert self.storage.records == [
            {
                "location": "test_client/i8t.instrument.test_decorator_introspect.Dummy.method",
                "start_ts": 1000,
                "finish_ts": 2000,
                "input": "fCQBr000000001elqie@VRC14luHAJl#B*zcVTj8bCi9QbuI",
                "output": "fCNhhE&",
            },
        ]

    def test_nested_function_introspected(self):
        dummy = Dummy()
        with mock.patch("time.time", side_effect=[1, 2, 3, 4]):
            result = dummy.nested(3)

        self.assertEqual(result, 12)
        assert self.storage.records == [
            {
                "location": "test_client/i8t.instrument.test_decorator_introspect.Dummy.nested.<locals>.func",
                "start_ts": 2,
                "finish_ts": 3,
                "input": "fCQBt000000001elqie@VRC14luH9k28NW325Wa=a%XdteUx=B",
                "output": "fCNhkE&",
            },
            {
                "location": "test_client/i8t.instrument.test_decorator_introspect.Dummy.nested",
                "start_ts": 1,
                "finish_ts": 4,
                "input": "fCQBr000000001elqie@VRC14luHAJl#B*zcVTj8bCi9QbuI",
                "output": "fCNhnE&",
            },
        ]

    def test_unregister_disables(self):
        # Disable introspect decorator and check that checkpoint is not sent
        self.decorator.unregister()
        self.assertEqual(dummy_func(1, 2), 3)
        assert not self.storage.records

    def test_exception_introspected(self):
        # Act & Assert
        with mock.patch("time.time", side_effect=[1000, 2000]):
            with self.assertRaises(ValueError):
                dummy_raise(1, 2)

        assert self.storage.records == [
            {
                "location": "test_client/i8t.instrument.test_decorator_introspect.dummy_raise",
                "start_ts": 1000,
                "finish_ts": 2000,
                "input": "fCQBt000000001elqie@VRC14luH3i0)~`~25Wa=a%XdteUx=B",
                "output": "fCQBt000000001el#B&sa&m8Sl#C8kWpi{OWq4y{aCB*JZj^H_",
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
