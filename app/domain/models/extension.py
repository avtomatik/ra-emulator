from pydantic import Field

from .base import DomainModel


class Extension(DomainModel):
    oid: str
    oid_description: str | None = None
    value: str
