import json

from app.config.paths import SEEDS_DIR
from app.dataset.models import Dataset
from app.domain.models.certificate import Certificate
from app.domain.models.certificate_request import CertificateRequest
from app.domain.models.user import User


def load_json(name: str):
    with (SEEDS_DIR / f"{name}.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def load_dataset() -> Dataset:
    return Dataset(
        certificates=tuple(
            Certificate.model_validate(x) for x in load_json("certificates")
        ),
        users=tuple(User.model_validate(x) for x in load_json("users")),
        cert_requests=tuple(
            CertificateRequest.model_validate(x)
            for x in load_json("cert_requests")
        ),
    )
