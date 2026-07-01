from uuid import UUID

from app.domain.models.certificate_request import CertificateRequest
from app.repositories.base import InMemoryRepository


class CertificateRequestRepository(InMemoryRepository[CertificateRequest]):
    def by_id(self, request_id: UUID) -> CertificateRequest | None:
        return self.find(lambda request: request.id == request_id)
