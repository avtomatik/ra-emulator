from uuid import UUID

from app.domain.models.certificate import Certificate
from app.repositories.base import InMemoryRepository


class CertificateRepository(InMemoryRepository[Certificate]):
    def by_id(self, certificate_id: UUID) -> Certificate | None:
        return self.find(lambda certificate: certificate.id == certificate_id)

    def by_serial(self, serial_number: str) -> Certificate | None:
        return self.find(
            lambda certificate: (certificate.serial_number == serial_number)
        )
