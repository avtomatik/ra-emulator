"""Thin repository adapter; the emulator does not require an ORM."""

from collections.abc import Callable
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from app.storage.sqlite import SQLiteStore

T = TypeVar("T", bound=BaseModel)


class SQLiteRepository(Generic[T]):
    kind: str
    model_type: type[T]
    id_field: str = "id"

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def all(self, *, folder: str | None = None) -> list[T]:
        return self.store.all(self.kind, self.model_type, folder=folder)

    def count(self) -> int:
        return self.store.count(self.kind)

    def by_id(self, record_id: UUID) -> T | None:
        return self.store.get(self.kind, record_id, self.model_type)

    def find(self, predicate: Callable[[T], bool]) -> T | None:
        return next(
            (record for record in self.all() if predicate(record)), None
        )

    def filter(self, predicate: Callable[[T], bool]) -> list[T]:
        return [record for record in self.all() if predicate(record)]
