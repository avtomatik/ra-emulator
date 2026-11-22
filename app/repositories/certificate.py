from app.domain.models.certificate import Certificate
from app.repositories.base import SQLiteRepository


class CertificateRepository(SQLiteRepository[Certificate]):
    kind = "certificates"
    model_type = Certificate

    def by_serial(self, serial_number: str) -> Certificate | None:
        return self.find(
            lambda certificate: certificate.serial_number == serial_number
        )
