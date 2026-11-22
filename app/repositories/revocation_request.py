from app.domain.models.revocation_request import RevocationRequest
from app.repositories.base import SQLiteRepository


class RevocationRequestRepository(SQLiteRepository[RevocationRequest]):
    kind = "rev_requests"
    model_type = RevocationRequest
    id_field = "rev_request_id"
