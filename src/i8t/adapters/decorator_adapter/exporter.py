import time

from i8t.client import IntrospectClient

from .serde import DecoratorSerde


class DecoratorExporter:
    def __init__(self, client: IntrospectClient) -> None:
        self._client = client
        self._serde = DecoratorSerde()

    def wrapper(self, func, *args, **kwargs):
        start_time = time.time()
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-except
            result = {"error": str(exc)}
            raise
        finally:
            self._send(
                f"{func.__module__}.{func.__qualname__}",
                {"args": args[1:] if self._is_method(func, args) else args, "kwargs": kwargs},
                result,
                start_time,
            )
        return result

    def _is_method(self, func, args) -> bool:
        if func.__qualname__ != func.__name__:
            # Could be method or nested function or both
            # https://peps.python.org/pep-3155/
            class_name = ""
            if args:
                class_name = args[0].__class__.__name__
            if func.__qualname__ == f"{class_name}.{func.__name__}":
                return True
        return False

    def _send(self, *args) -> None:
        self._client.send(self._client.make_checkpoint(*self._serde.serialize(*args)))
