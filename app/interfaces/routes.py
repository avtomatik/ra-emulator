from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.dto.certificate import CertificateDetailDTO, CertificateSummaryDTO
from app.api.dto.certificate_request import (CertificateRequestDetailDTO,
                                             CertificateRequestSummaryDTO)
from app.api.dto.pagination import PageResult
from app.api.dto.revocation_request import (CreateRevocationRequestDTO,
                                            ResolveRevocationRequestDTO,
                                            RevocationRequestDetailDTO,
                                            RevocationRequestSummaryDTO)
from app.api.dto.user import UserSummaryDTO
from app.application.certificate_requests import CertificateRequestService
from app.application.certificates import CertificateService
from app.application.revocation_requests import RevocationRequestService
from app.application.users import UserService

router = APIRouter()


def build_router(
    *,
    certificates: CertificateService,
    certificate_requests: CertificateRequestService,
    users: UserService,
    revocation_requests: RevocationRequestService,
) -> APIRouter:
    api = APIRouter()

    @api.get(
        "/certificates",
        response_model=PageResult[CertificateSummaryDTO],
        response_model_exclude_none=True,
    )
    def list_certificates(
        q: str | None = Query(default=None),
        value: str | None = Query(default=None),
        page_token: str | None = Query(default=None, alias="pageToken"),
        folder: str | None = Query(default=None),
    ):
        return certificates.list(
            query=q if q is not None else value,
            page_token=page_token,
            folder=folder,
            search_parameter="q" if q is not None else "value",
        )

    @api.get(
        "/certificates/{certificate_id}",
        response_model=CertificateDetailDTO,
        response_model_exclude_none=True,
    )
    def get_certificate(certificate_id: UUID):
        certificate = certificates.get(certificate_id)
        if certificate is None:
            raise HTTPException(
                status_code=404, detail="Certificate not found"
            )
        return certificate

    @api.get(
        "/certRequests",
        response_model=PageResult[CertificateRequestSummaryDTO],
        response_model_exclude_none=True,
    )
    def list_certificate_requests(
        q: str | None = Query(default=None),
        page_token: str | None = Query(default=None, alias="pageToken"),
    ):
        return certificate_requests.list(query=q, page_token=page_token)

    @api.get(
        "/certRequests/{request_id}",
        response_model=CertificateRequestDetailDTO,
        response_model_exclude_none=True,
    )
    def get_certificate_request(request_id: UUID):
        request = certificate_requests.get(request_id)
        if request is None:
            raise HTTPException(
                status_code=404, detail="Certificate request not found"
            )
        return request

    @api.get(
        "/revRequests",
        response_model=PageResult[RevocationRequestSummaryDTO],
        response_model_exclude_none=True,
    )
    def list_revocation_requests(
        q: str | None = Query(default=None),
        value: str | None = Query(default=None),
        page_token: str | None = Query(default=None, alias="pageToken"),
        folder: str | None = Query(default=None),
    ):
        return revocation_requests.list(
            query=q if q is not None else value,
            page_token=page_token,
            folder=folder,
            search_parameter="q" if q is not None else "value",
        )

    @api.post(
        "/revRequests",
        response_model=RevocationRequestDetailDTO,
        response_model_exclude_none=True,
        status_code=201,
    )
    def create_revocation_request(body: CreateRevocationRequestDTO):
        return revocation_requests.create(body)

    @api.post(
        "/revRequests/{request_id}/approve",
        response_model=RevocationRequestDetailDTO,
        response_model_exclude_none=True,
    )
    def approve_revocation_request(
        request_id: UUID, body: ResolveRevocationRequestDTO | None = None
    ):
        return revocation_requests.approve(
            request_id, body or ResolveRevocationRequestDTO()
        )

    @api.post(
        "/revRequests/{request_id}/reject",
        response_model=RevocationRequestDetailDTO,
        response_model_exclude_none=True,
    )
    def reject_revocation_request(
        request_id: UUID, body: ResolveRevocationRequestDTO | None = None
    ):
        return revocation_requests.reject(
            request_id, body or ResolveRevocationRequestDTO()
        )

    @api.get(
        "/revRequests/{request_id}",
        response_model=RevocationRequestDetailDTO,
        response_model_exclude_none=True,
    )
    def get_revocation_request(request_id: UUID):
        request = revocation_requests.get(request_id)
        if request is None:
            raise HTTPException(
                status_code=404, detail="Revocation request not found"
            )
        return request

    @api.get(
        "/users",
        response_model=PageResult[UserSummaryDTO],
        response_model_exclude_none=True,
    )
    def list_users(
        q: str | None = Query(default=None),
        page_token: str | None = Query(default=None, alias="pageToken"),
    ):
        return users.list(query=q, page_token=page_token)

    @api.get(
        "/users/{user_id}",
        response_model=UserSummaryDTO,
        response_model_exclude_none=True,
    )
    def get_user(user_id: UUID):
        user = users.get(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    return api
