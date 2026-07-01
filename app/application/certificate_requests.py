from uuid import UUID

from app.api.dto.certificate_request import (CertificateRequestDetailDTO,
                                             CertificateRequestSummaryDTO)
from app.api.dto.pagination import PageResult
from app.api.presenters.certificate_request import (
    certificate_request_detail, certificate_request_summaries)
from app.emulator.paginator import Paginator
from app.repositories.certificate_request import CertificateRequestRepository


class CertificateRequestService:
    RESOURCE = "/certRequests"

    def __init__(
        self, repository: CertificateRequestRepository, *, api_root: str
    ) -> None:
        self.repository = repository
        self.endpoint = f"{api_root}{self.RESOURCE}"

    def list(
        self, *, query: str | None, page_token: str | None
    ) -> PageResult[CertificateRequestSummaryDTO]:
        requests = self.repository.all()
        if query:
            requests = self._filter(requests, query)
        page = Paginator.paginate(
            items=requests, page_token=page_token, endpoint=self.endpoint
        )
        return PageResult(
            items=certificate_request_summaries(page.items), links=page.links
        )

    def get(self, request_id: UUID) -> CertificateRequestDetailDTO | None:
        request = self.repository.by_id(request_id)
        if request is None:
            return None
        return certificate_request_detail(request)

    @staticmethod
    def _filter(requests, query: str):
        query = query.casefold()
        return [
            request
            for request in requests
            if (
                query in (request.name_attributes.common_name or "").casefold()
            )
        ]
