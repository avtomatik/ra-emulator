from app.api.dto.certificate_request import (CertificateRequestDetailDTO,
                                             CertificateRequestSummaryDTO)
from app.domain.models.certificate_request import CertificateRequest


def certificate_request_summary(
    certificate_request: CertificateRequest,
) -> CertificateRequestSummaryDTO:
    return CertificateRequestSummaryDTO.model_validate(
        certificate_request, from_attributes=True
    )


def certificate_request_summaries(
    certificate_requests: list[CertificateRequest],
) -> list[CertificateRequestSummaryDTO]:
    return [
        certificate_request_summary(certificate_request)
        for certificate_request in certificate_requests
    ]


def certificate_request_detail(
    certificate_request: CertificateRequest,
) -> CertificateRequestDetailDTO:
    return CertificateRequestDetailDTO.model_validate(
        certificate_request, from_attributes=True
    )
