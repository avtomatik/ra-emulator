from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    def __init__(self, items: Iterable[T]) -> None:
        self._items = list(items)

    def all(self) -> list[T]:
        return list(self._items)

    def count(self) -> int:
        return len(self._items)

    def find(self, predicate: Callable[[T], bool]) -> T | None:
        for item in self._items:
            if predicate(item):
                return item
        return None

    def filter(self, predicate: Callable[[T], bool]) -> list[T]:
        return [item for item in self._items if predicate(item)]
