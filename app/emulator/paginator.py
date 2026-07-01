import base64
import hashlib
import struct
from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

from app.api.dto.pagination import Links, NextLink
from app.emulator.errors import InvalidPageToken

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Page(Generic[T]):
    items: list[T]
    links: Links | None


class Paginator:
    DEFAULT_PAGE_SIZE = 20

    @classmethod
    def paginate(
        cls,
        *,
        items: Sequence[T],
        page_token: str | None,
        endpoint: str,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Page[T]:
        offset = cls.decode(page_token)
        page = list(items[offset : offset + page_size])
        next_offset = offset + len(page)
        if next_offset >= len(items):
            return Page(items=page, links=None)
        token = cls.encode(next_offset)
        return Page(
            items=page,
            links=Links(next=NextLink(href=f"{endpoint}?pageToken={token}")),
        )

    @staticmethod
    def encode(offset: int) -> str:
        if offset < 0:
            raise ValueError("Offset cannot be negative")
        # 4-byte cursor fields.
        #
        # These are deliberately deterministic and monotonically
        # decreasing, to resemble the observed API.
        field1 = 27_200_000 - offset * 1_000
        field2 = 148_900_000 - offset * 100
        # Deterministic opaque-looking middle section.
        digest = hashlib.sha256(f"page-token:{offset}".encode()).digest()[:16]
        raw = struct.pack("<I", field1) + digest + struct.pack("<I", field2)
        # 24 bytes -> 32 Base64URL characters
        assert len(raw) == 24
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    @staticmethod
    def decode(token: str | None) -> int:
        if not token:
            return 0
        try:
            # Restore Base64 padding.
            padded = token + "=" * (-len(token) % 4)
            raw = base64.urlsafe_b64decode(padded)
            if len(raw) != 24:
                raise ValueError
            field1 = struct.unpack("<I", raw[:4])[0]
            # Reverse our encoding.
            offset = (27_200_000 - field1) // 1_000
            if offset < 0:
                raise ValueError
            return offset
        except (ValueError, struct.error, UnicodeDecodeError) as exc:
            raise InvalidPageToken("Invalid page token") from exc
