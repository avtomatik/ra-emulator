from uuid import UUID

from app.domain.models.revocation_request import RevocationRequest
from app.repositories.base import InMemoryRepository


class RevocationRequestRepository(InMemoryRepository[RevocationRequest]):
    def by_id(self, request_id: UUID) -> RevocationRequest | None:
        return self.find(lambda request: request.id == request_id)
