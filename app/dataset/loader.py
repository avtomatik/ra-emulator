import json
import logging

from app.config.paths import SEEDS_DIR
from app.dataset.models import Dataset
from app.domain.models.certificate import Certificate
from app.domain.models.certificate_request import CertificateRequest
from app.domain.models.revocation_request import RevocationRequest
from app.domain.models.user import User

logger = logging.getLogger(__name__)


def load_json(name: str):
    with (SEEDS_DIR / f"{name}.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def load_dataset(*, default_folder: str = "default") -> Dataset:
    # Old seeds without folder metadata remain in the first (legacy) folder.
    # Missing rev_requests.json is accepted for pre-revocation seed snapshots.
    revocation_path = SEEDS_DIR / "rev_requests.json"
    revocation_items = (
        load_json("rev_requests") if revocation_path.exists() else []
    )

    # Pre-implementation generator outputs were placeholders, not valid RA
    # records. Do not prevent an older certificate-only seed snapshot booting.
    def is_legacy_placeholder(item: dict) -> bool:
        return (
            item.get("status") == "RevocationRequestStatus:TO_DO"
            and item.get("serialNumber") == "to-do"
        )

    valid_items = [
        item for item in revocation_items if not is_legacy_placeholder(item)
    ]
    if len(valid_items) != len(revocation_items):
        logger.warning(
            "Ignoring %s legacy placeholder revocation requests; "
            "regenerate seeds to enable revocation endpoints.",
            len(revocation_items) - len(valid_items),
        )
    revocation_items = valid_items
    certificates = tuple(
        Certificate.model_validate(
            {**item, "folder": item.get("folder") or default_folder}
        )
        for item in load_json("certificates")
    )
    folders_by_certificate = {
        str(item.id): item.folder for item in certificates
    }
    return Dataset(
        certificates=certificates,
        users=tuple(User.model_validate(x) for x in load_json("users")),
        cert_requests=tuple(
            CertificateRequest.model_validate(x)
            for x in load_json("cert_requests")
        ),
        rev_requests=tuple(
            RevocationRequest.model_validate(
                {
                    **x,
                    "folder": x.get("folder")
                    or folders_by_certificate.get(
                        str(x.get("certificateId")), default_folder
                    ),
                }
            )
            for x in revocation_items
        ),
    )
