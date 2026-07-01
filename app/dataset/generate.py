import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from random import Random

from faker import Faker

from app.config.paths import SEEDS_DIR
from app.dataset.crypto import build_x509_certificate
from app.domain.constants.enums import Gender
from app.domain.constants.oids import OID

fake = Faker("ru_RU")


def write(name, data):
    with (SEEDS_DIR / f"{name}.json").open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def make_user(rng: Random):
    gender = rng.choice(list(Gender))
    if gender == Gender.FEMALE:
        first = fake.first_name_female()
        middle = fake.middle_name_female()
        last = fake.last_name_female()
    else:
        first = fake.first_name_male()
        middle = fake.middle_name_male()
        last = fake.last_name_male()
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
        "createdWhen": datetime.now(timezone.utc).isoformat(),
        "distinguishedName": f"CN={cn},O={fake.company()}",
    }


def make_request(user, rng: Random):
    created = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "nameAttributes": user["nameAttributes"],
        "createdWhen": created.isoformat(),
        "status": "APPROVED",
        "seed": rng.randint(1000, 9999),
    }


def make_certificate(user, request, rng: Random):
    now = datetime.now(timezone.utc)
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


def main(number: int = 100, seed: int = 42):
    rng = Random(seed)
    Faker.seed(seed)
    users = []
    requests = []
    certs = []
    for _ in range(number):
        user = make_user(rng)
        req = make_request(user, rng)
        cert = make_certificate(user, req, rng)
        users.append(user)
        requests.append(req)
        certs.append(cert)
    write("users", users)
    write("cert_requests", requests)
    write("certificates", certs)
    print("✔ deterministic dataset generated")
    print(f"users={len(users)}")
    print(f"requests={len(requests)}")
    print(f"certificates={len(certs)}")


if __name__ == "__main__":
    main()
