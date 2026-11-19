from datetime import datetime
from uuid import UUID

from app.domain.constants.enums import (RevocationReason,
                                        RevocationRequestStatus)
from app.domain.models.base import DomainModel


class RevocationRequest(DomainModel):
    rev_request_id: UUID
    created_when: datetime
    resolved_when: datetime
    auth_replied_when: datetime
    serial_number: str
    thumbprint: str
    status: RevocationRequestStatus
    certificate_id: UUID | None = None
    user_id: UUID | None = None
    creator_id: UUID | None = None
    creator_name: str | None = None
    creator_login: str | None = None
    resolver_id: UUID | None = None
    resolver_name: str | None = None
    resolver_login: str | None = None
    revocation_reason: RevocationReason | None = None
    raw_request: bytes | None = None
    folder: str | None = None
