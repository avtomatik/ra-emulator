"""Revocation query and lifecycle use cases.
The state machine is emulator-defined until a production RA write contract is
available. Database operations, not HTTP requests, enforce its invariants.
"""

from uuid import UUID

from app.api.dto.pagination import PageResult
from app.api.dto.revocation_request import (CreateRevocationRequestDTO,
                                            ResolveRevocationRequestDTO,
                                            RevocationRequestDetailDTO,
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
        self,
        *,
        query: str | None,
        page_token: str | None,
        folder: str | None = None,
        search_parameter: str = "q",
    ) -> PageResult[RevocationRequestSummaryDTO]:
        requests = self.repository.all(folder=folder)
        if query:
            requests = self._filter(requests, query)
        parameters = {}
        if folder is not None:
            parameters["folder"] = folder
        if query:
            parameters[search_parameter] = query
        page = Paginator.paginate(
            items=requests,
            page_token=page_token,
            endpoint=self.endpoint,
            query_params=parameters,
        )
        return PageResult(
            items=revocation_request_summaries(page.items), links=page.links
        )

    def get(self, request_id: UUID) -> RevocationRequestDetailDTO | None:
        request = self.repository.by_id(request_id)
        return (
            revocation_request_detail(request) if request is not None else None
        )

    def create(
        self, body: CreateRevocationRequestDTO
    ) -> RevocationRequestDetailDTO:
        request = self.repository.store.create_revocation(
            certificate_id=body.certificate_id,
            reason=body.revocation_reason,
            creator_id=body.creator_id,
        )
        return revocation_request_detail(request)

    def approve(
        self, request_id: UUID, body: ResolveRevocationRequestDTO
    ) -> RevocationRequestDetailDTO:
        return self._resolve(request_id, body, approve=True)

    def reject(
        self, request_id: UUID, body: ResolveRevocationRequestDTO
    ) -> RevocationRequestDetailDTO:
        return self._resolve(request_id, body, approve=False)

    def _resolve(
        self,
        request_id: UUID,
        body: ResolveRevocationRequestDTO,
        *,
        approve: bool,
    ) -> RevocationRequestDetailDTO:
        return revocation_request_detail(
            self.repository.store.resolve_revocation(
                request_id, approve=approve, resolver_id=body.resolver_id
            )
        )

    @staticmethod
    def _filter(requests, query: str):
        query = query.casefold()
        return [
            request
            for request in requests
            if query in request.serial_number.casefold()
            or query in request.thumbprint.casefold()
            or query in str(request.rev_request_id).casefold()
        ]
