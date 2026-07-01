from uuid import UUID

from app.api.dto.certificate import CertificateDetailDTO, CertificateSummaryDTO
from app.api.dto.pagination import PageResult
from app.api.presenters.certificate import (certificate_detail,
                                            certificate_summaries)
from app.emulator.paginator import Paginator
from app.repositories.certificate import CertificateRepository


class CertificateService:
    RESOURCE = "/certificates"

    def __init__(
        self, repository: CertificateRepository, *, api_root: str
    ) -> None:
        self.repository = repository
        self.endpoint = f"{api_root}{self.RESOURCE}"

    def list(
        self, *, query: str | None, page_token: str | None
    ) -> PageResult[CertificateSummaryDTO]:
        certificates = self.repository.all()
        if query:
            certificates = self._filter(certificates, query)
        page = Paginator.paginate(
            items=certificates, page_token=page_token, endpoint=self.endpoint
        )
        return PageResult(
            items=certificate_summaries(page.items), links=page.links
        )

    def get(self, certificate_id: UUID) -> CertificateDetailDTO | None:
        certificate = self.repository.by_id(certificate_id)
        if certificate is None:
            return None
        return certificate_detail(certificate)

    @staticmethod
    def _filter(certificates, query: str):
        query = query.casefold()
        return [
            certificate
            for certificate in certificates
            if (
                query in certificate.serial_number.casefold()
                or query in certificate.thumbprint.casefold()
                or query
                in (certificate.name_attributes.common_name or "").casefold()
            )
        ]
