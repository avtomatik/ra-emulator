from app.domain.models.certificate_request import CertificateRequest
from app.repositories.base import SQLiteRepository


class CertificateRequestRepository(SQLiteRepository[CertificateRequest]):
    kind = "cert_requests"
    model_type = CertificateRequest
