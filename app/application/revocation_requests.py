from uuid import UUID

from app.api.dto.pagination import PageResult
from app.api.dto.revocation_request import (RevocationRequestDetailDTO,
                                            RevocationRequestSummaryDTO)
from app.api.presenters.revocation_request import (
    revocation_request_detail, revocation_request_summaries)
from app.emulator.paginator import Paginator
from app.repositories.revocation_request import RevocationRequestRepository


class RevocationRequestService:
    RESOURCE = "/revRequests"

    def __init__(
        self, repository: RevocationRequestRepository, *, api_root: str
    ) -> None:
        self.repository = repository
        self.endpoint = f"{api_root}{self.RESOURCE}"

    def list(
        self, *, query: str | None, page_token: str | None
    ) -> PageResult[RevocationRequestSummaryDTO]:
        requests = self.repository.all()
        if query:
            requests = self._filter(requests, query)
        page = Paginator.paginate(
            items=requests, page_token=page_token, endpoint=self.endpoint
        )
        return PageResult(
            items=revocation_request_summaries(page.items), links=page.links
        )

    def get(self, request_id: UUID) -> RevocationRequestDetailDTO | None:
        request = self.repository.by_id(request_id)
        if request is None:
            return None
        return revocation_request_detail(request)

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
