import hashlib
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ObjectIdentifier


def build_subject(name_attributes: dict[str, str]) -> x509.Name:
    attributes = []
    for oid, value in name_attributes.items():
        attributes.append(
            x509.NameAttribute(ObjectIdentifier(str(oid)), value)
        )
    return x509.Name(attributes)


def deterministic_int(seed: str) -> int:
    h = hashlib.sha256(seed.encode()).hexdigest()
    return int(h[:16], 16)


def generate_keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def build_x509_certificate(
    *,
    subject_attributes: dict[str, str],
    serial: str,
    not_before: datetime,
    not_after: datetime,
    issuer_name: str,
):
    private_key = generate_keypair()
    subject = build_subject(subject_attributes)
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer_name)])
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(certificate_serial(serial))
        .not_valid_before(not_before)
        .not_valid_after(not_after)
    )
    cert = cert_builder.sign(
        private_key=private_key, algorithm=hashes.SHA256()
    )
    der = cert.public_bytes(serialization.Encoding.DER)
    return cert, der


def certificate_serial(serial_text: str) -> int:
    value = deterministic_int(serial_text)
    if value <= 0:
        value = 1
    return value
