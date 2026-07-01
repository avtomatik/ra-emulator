from dataclasses import dataclass

from app.domain.models.certificate import Certificate
from app.domain.models.certificate_request import CertificateRequest
from app.domain.models.user import User


@dataclass(frozen=True, slots=True)
class Dataset:
    certificates: tuple[Certificate, ...]
    cert_requests: tuple[CertificateRequest, ...]
    users: tuple[User, ...]
