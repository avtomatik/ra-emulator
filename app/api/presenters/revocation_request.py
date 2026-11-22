from app.api.dto.revocation_request import (RevocationRequestDetailDTO,
                                            RevocationRequestSummaryDTO)
from app.domain.models.revocation_request import RevocationRequest


def revocation_request_summary(
    revocation_request: RevocationRequest,
) -> RevocationRequestSummaryDTO:
    return RevocationRequestSummaryDTO.model_validate(
        revocation_request, from_attributes=True
    )


def revocation_request_summaries(
    revocation_requests: list[RevocationRequest],
) -> list[RevocationRequestSummaryDTO]:
    return [
        revocation_request_summary(revocation_request)
        for revocation_request in revocation_requests
    ]


def revocation_request_detail(
    revocation_request: RevocationRequest,
) -> RevocationRequestDetailDTO:
    return RevocationRequestDetailDTO.model_validate(
        revocation_request, from_attributes=True
    )
