from app.api.dto.certificate import CertificateDetailDTO, CertificateSummaryDTO
from app.domain.models.certificate import Certificate


def certificate_summary(certificate: Certificate) -> CertificateSummaryDTO:
    return CertificateSummaryDTO.model_validate(
        certificate, from_attributes=True
    )


def certificate_summaries(
    certificates: list[Certificate],
) -> list[CertificateSummaryDTO]:
    return [certificate_summary(certificate) for certificate in certificates]


def certificate_detail(certificate: Certificate) -> CertificateDetailDTO:
    return CertificateDetailDTO.model_validate(
        certificate, from_attributes=True
    )
