from functools import wraps
from typing import Optional

from i8t.adapters.decorator_adapter.exporter import DecoratorExporter
from i8t.client import IntrospectClient


class DecoratorIntrospect:
    instance: Optional["DecoratorIntrospect"] = None

    def __init__(self, client: IntrospectClient) -> None:
        self._client = client
        self._decorator_exporter = DecoratorExporter(client)

    def register(self) -> None:
        self.__class__.instance = self

    def unregister(self) -> None:
        self.__class__.instance = None

    def wrapper(self, func, *args, **kwargs):
        return self._decorator_exporter.wrapper(func, *args, **kwargs)


def introspect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if DecoratorIntrospect.instance:
            return DecoratorIntrospect.instance.wrapper(func, *args, **kwargs)
        return func(*args, **kwargs)

    return wrapper
