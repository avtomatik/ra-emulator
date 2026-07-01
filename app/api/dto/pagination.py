from typing import Generic, TypeVar

from pydantic import Field

from .base import DTOModel


class NextLink(DTOModel):
    href: str


class Links(DTOModel):
    next: NextLink | None = None


T = TypeVar("T")


class PageResult(DTOModel, Generic[T]):
    items: list[T]
    links: Links | None = Field(default=None, alias="_links")
