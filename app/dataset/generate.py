import base64
import uuid
from datetime import datetime, timedelta, timezone
from random import Random

from faker import Faker

from app.config.settings import Settings, get_settings
from app.dataset.crypto import build_x509_certificate
from app.dataset.models import Dataset
from app.domain.constants.enums import Gender
from app.domain.constants.oids import OID
from app.domain.models.certificate import Certificate
from app.domain.models.certificate_request import CertificateRequest
from app.domain.models.revocation_request import RevocationRequest
from app.domain.models.user import User
from app.storage.sqlite import SQLiteStore

fake = Faker("ru_RU")


def make_user(rng: Random):
    gender = rng.choice(list(Gender))
    if gender == Gender.FEMALE:
        first, middle, last = (
            fake.first_name_female(),
            fake.middle_name_female(),
            fake.last_name_female(),
        )
    else:
        first, middle, last = (
            fake.first_name_male(),
            fake.middle_name_male(),
            fake.last_name_male(),
        )
    cn = f"{last} {first} {middle}"
    return {
        "id": str(uuid.uuid4()),
        "nameAttributes": {
            OID.CN: cn,
            OID.SN: last,
            OID.GIVEN_NAME: first,
            OID.C: "RU",
            OID.INN: fake.individuals_inn(),
            OID.SNILS: fake.snils(),
            OID.T: fake.job(),
            OID.GUID: fake.numerify(text="#" * 6),
        },
        "createdWhen": (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat(),
        "distinguishedName": f"CN={cn},O={fake.company()}",
    }


def make_cert_request(user, rng: Random):
    created = datetime.now(timezone.utc) - timedelta(minutes=90)
    return {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "nameAttributes": user["nameAttributes"],
        "createdWhen": created.isoformat(),
        "status": "APPROVED",
        "seed": rng.randint(1000, 9999),
    }


def make_certificate(user, request, rng: Random):
    now = datetime.now(timezone.utc) - timedelta(hours=1)
    serial = fake.hexify(text="^" * 34)
    not_before = now - timedelta(days=1)
    not_after = now + timedelta(days=365)
    name_attributes = dict(user["nameAttributes"])
    common_name = name_attributes.get(OID.CN)
    if common_name:
        name_attributes[OID.CN] = common_name[:64]
    cert, der = build_x509_certificate(
        subject_attributes=name_attributes,
        serial=serial,
        not_before=not_before,
        not_after=not_after,
        issuer_name="RA-EMULATOR-CA",
    )
    return {
        "id": str(uuid.uuid4()),
        "serialNumber": serial,
        "thumbprint": cert.fingerprint(cert.signature_hash_algorithm).hex(),
        "nameAttributes": user["nameAttributes"],
        "createdWhen": now.isoformat(),
        "notBefore": not_before.isoformat(),
        "notAfter": not_after.isoformat(),
        "keyNotAfter": not_after.isoformat(),
        "status": "VALID",
        "userId": user["id"],
        "certRequestId": request["id"],
        "subject": user["distinguishedName"],
        "rawCertificate": base64.b64encode(der).decode("utf-8"),
    }


def make_rev_request(user, cert):
    """Create a completed request referring to a real revoked certificate."""
    created = datetime.now(timezone.utc) - timedelta(minutes=20)
    resolved = created + timedelta(minutes=5)
    auth_replied = resolved + timedelta(minutes=1)
    return {
        "revRequestId": str(uuid.uuid4()),
        "createdWhen": created.isoformat(),
        "resolvedWhen": resolved.isoformat(),
        "authRepliedWhen": auth_replied.isoformat(),
        "serialNumber": cert["serialNumber"],
        "thumbprint": cert["thumbprint"],
        "status": "Completed",
        "certificateId": cert["id"],
        "userId": user["id"],
        "revocationReason": "KeyCompromise",
        "folder": cert["folder"],
    }


def build_dataset(
    number: int = 100,
    seed: int = 42,
    *,
    folders: tuple[str, ...] = ("default",),
) -> Dataset:
    rng = Random(seed)
    Faker.seed(seed)
    if not folders:
        raise ValueError("At least one folder is required")
    users = []
    cert_requests = []
    certs = []
    rev_requests = []
    for index in range(number):
        user = make_user(rng)
        cert_request = make_cert_request(user, rng)
        cert = make_certificate(user, cert_request, rng)
        cert["folder"] = folders[index % len(folders)]
        # A deterministic subset of certificates has completed revocations.
        if index % 3 == 0:
            rev_request = make_rev_request(user, cert)
            cert["status"] = "Revoked"
            cert["revokedWhen"] = rev_request["resolvedWhen"]
            cert["revocationReason"] = rev_request["revocationReason"]
            rev_requests.append(rev_request)
        users.append(user)
        cert_requests.append(cert_request)
        certs.append(cert)
    return Dataset(
        users=tuple(User.model_validate(item) for item in users),
        cert_requests=tuple(
            CertificateRequest.model_validate(item) for item in cert_requests
        ),
        certificates=tuple(Certificate.model_validate(item) for item in certs),
        rev_requests=tuple(
            RevocationRequest.model_validate(item) for item in rev_requests
        ),
    )


def main(
    number: int = 100,
    seed: int = 42,
    *,
    folders: tuple[str, ...] | None = None,
    settings: Settings | None = None,
) -> None:
    """Explicit destructive reset of the SQLite seed dataset."""
    settings = settings or get_settings()
    dataset = build_dataset(
        number=number,
        seed=seed,
        folders=folders or settings.certificate_folders,
    )
    store = SQLiteStore(settings.database_path)
    store.initialize()
    store.replace_dataset(dataset)
    print("✔ seeded dataset generated")
    print(f"users={len(dataset.users)}")
    print(f"cert_requests={len(dataset.cert_requests)}")
    print(f"certificates={len(dataset.certificates)}")
    print(f"rev_requests={len(dataset.rev_requests)}")


if __name__ == "__main__":
    main()
