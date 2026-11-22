"""SQLite persistence for synthetic RA records.
Records retain their versionable API payloads as JSON, while SQLite provides
indexes, stable insertion ordering, durability, and atomic workflow updates.
This is intentionally not a production RA database.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel

from app.domain.constants.enums import (RevocationReason,
                                        RevocationRequestStatus)
from app.domain.models.certificate import Certificate
from app.domain.models.revocation_request import RevocationRequest

T = TypeVar("T", bound=BaseModel)
KINDS = ("certificates", "cert_requests", "rev_requests", "users")


class WorkflowConflict(Exception):
    """Invalid lifecycle transition or a conflicting revocation."""


class WorkflowNotFound(Exception):
    """Requested certificate or revocation request does not exist."""


class SQLiteStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=15000")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            # WAL lets independent HTTP clients read during a write transaction.
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS records (
                    ordinal INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    folder TEXT,
                    payload TEXT NOT NULL,
                    UNIQUE(kind, record_id)
                );
                CREATE INDEX IF NOT EXISTS idx_records_kind_folder
                    ON records(kind, folder, ordinal);
            """
            )

    @staticmethod
    def _select(
        conn: sqlite3.Connection, kind: str, record_id: UUID | str
    ) -> sqlite3.Row | None:
        return conn.execute(
            "SELECT payload FROM records WHERE kind=? AND record_id=?",
            (kind, str(record_id)),
        ).fetchone()

    @staticmethod
    def _put(
        conn: sqlite3.Connection,
        kind: str,
        record: BaseModel,
        *,
        id_field: str,
    ) -> None:
        record_id = str(getattr(record, id_field))
        folder = getattr(record, "folder", None)
        conn.execute(
            """INSERT INTO records (kind, record_id, folder, payload)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(kind, record_id) DO UPDATE SET
                folder=excluded.folder, payload=excluded.payload""",
            (
                kind,
                record_id,
                folder,
                record.model_dump_json(by_alias=False, exclude_none=True),
            ),
        )

    def count(self, kind: str) -> int:
        with self.connection() as conn:
            return conn.execute(
                "SELECT count(*) FROM records WHERE kind=?", (kind,)
            ).fetchone()[0]

    def all(
        self, kind: str, model_type: type[T], *, folder: str | None = None
    ) -> list[T]:
        with self.connection() as conn:
            if folder is None:
                rows = conn.execute(
                    "SELECT payload FROM records WHERE kind=? ORDER BY ordinal",
                    (kind,),
                )
            else:
                rows = conn.execute(
                    "SELECT payload FROM records WHERE kind=? AND folder=? ORDER BY ordinal",
                    (kind, folder),
                )
            return [model_type.model_validate_json(row[0]) for row in rows]

    def get(self, kind: str, record_id: UUID, model_type: type[T]) -> T | None:
        with self.connection() as conn:
            row = self._select(conn, kind, record_id)
            return (
                model_type.model_validate_json(row[0])
                if row is not None
                else None
            )

    def replace_dataset(self, dataset) -> None:
        """Explicit seed reset: replace all records as a single transaction."""
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("DELETE FROM records")
                for kind, values, id_field in (
                    ("users", dataset.users, "id"),
                    ("cert_requests", dataset.cert_requests, "id"),
                    ("certificates", dataset.certificates, "id"),
                    ("rev_requests", dataset.rev_requests, "rev_request_id"),
                ):
                    for record in values:
                        self._put(conn, kind, record, id_field=id_field)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def create_revocation(
        self,
        *,
        certificate_id: UUID,
        reason: RevocationReason,
        creator_id: UUID | None = None,
    ) -> RevocationRequest:
        """One pending request per certificate, with serialized writers."""
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = self._select(conn, "certificates", certificate_id)
                if row is None:
                    raise WorkflowNotFound("Certificate not found")
                cert = Certificate.model_validate_json(row[0])
                if cert.status.casefold() != "valid":
                    raise WorkflowConflict(
                        "Certificate cannot be revoked in its current state"
                    )
                rows = conn.execute(
                    "SELECT payload FROM records WHERE kind='rev_requests'"
                )
                for existing_row in rows:
                    existing = RevocationRequest.model_validate_json(
                        existing_row[0]
                    )
                    if (
                        existing.certificate_id == certificate_id
                        and existing.status
                        in (
                            RevocationRequestStatus.PENDING,
                            RevocationRequestStatus.COMPLETED,
                        )
                    ):
                        raise WorkflowConflict(
                            "An active or completed revocation request already exists"
                        )
                request = RevocationRequest(
                    rev_request_id=uuid4(),
                    created_when=datetime.now(timezone.utc),
                    resolved_when=None,
                    auth_replied_when=None,
                    serial_number=cert.serial_number,
                    thumbprint=cert.thumbprint,
                    status=RevocationRequestStatus.PENDING,
                    certificate_id=cert.id,
                    user_id=cert.user_id,
                    creator_id=creator_id,
                    revocation_reason=reason,
                    folder=cert.folder,
                )
                self._put(
                    conn, "rev_requests", request, id_field="rev_request_id"
                )
                conn.commit()
                return request
            except Exception:
                conn.rollback()
                raise

    def resolve_revocation(
        self,
        request_id: UUID,
        *,
        approve: bool,
        resolver_id: UUID | None = None,
    ) -> RevocationRequest:
        """Commit request resolution and the certificate's status atomically."""
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = self._select(conn, "rev_requests", request_id)
                if row is None:
                    raise WorkflowNotFound("Revocation request not found")
                request = RevocationRequest.model_validate_json(row[0])
                if request.status != RevocationRequestStatus.PENDING:
                    raise WorkflowConflict(
                        "Only pending requests can be resolved"
                    )
                cert_row = self._select(
                    conn, "certificates", request.certificate_id
                )
                if cert_row is None:
                    raise WorkflowConflict(
                        "Linked certificate no longer exists"
                    )
                cert = Certificate.model_validate_json(cert_row[0])
                if approve and cert.status.casefold() != "valid":
                    raise WorkflowConflict(
                        "Only valid certificates can be revoked"
                    )
                now = datetime.now(timezone.utc)
                request.status = (
                    RevocationRequestStatus.COMPLETED
                    if approve
                    else RevocationRequestStatus.REJECTED
                )
                request.resolved_when = now
                request.auth_replied_when = now
                request.resolver_id = resolver_id
                self._put(
                    conn, "rev_requests", request, id_field="rev_request_id"
                )
                if approve:
                    cert.status = "Revoked"
                    cert.revoked_when = now
                    cert.revocation_reason = request.revocation_reason.value
                    self._put(conn, "certificates", cert, id_field="id")
                conn.commit()
                return request
            except Exception:
                conn.rollback()
                raise
