from fastapi import FastAPI
from pydantic_settings import BaseSettings

from app.application.certificate_requests import CertificateRequestService
from app.application.certificates import CertificateService
from app.application.users import UserService
from app.config.settings import Settings
from app.dataset.ensure import ensure_dataset_exists
from app.dataset.loader import load_dataset
from app.emulator.errors import install_exception_handlers
from app.emulator.latency import install_latency
from app.interfaces.health import router as health_router
from app.interfaces.routes import build_router
from app.repositories.certificate import CertificateRepository
from app.repositories.certificate_request import CertificateRequestRepository
from app.repositories.user import UserRepository


def create_app(settings: BaseSettings | None = None) -> FastAPI:
    settings = settings or Settings()
    ensure_dataset_exists()
    dataset = load_dataset()
    certificate_repository = CertificateRepository(dataset.certificates)
    certificate_request_repository = CertificateRequestRepository(
        dataset.cert_requests
    )
    user_repository = UserRepository(dataset.users)
    certificate_service = CertificateService(
        certificate_repository, api_root=settings.api_root
    )
    certificate_request_service = CertificateRequestService(
        certificate_request_repository, api_root=settings.api_root
    )
    user_service = UserService(user_repository, api_root=settings.api_root)
    app = FastAPI(title="RA Contract Emulator", version="1.0.0")
    app.include_router(
        build_router(
            certificates=certificate_service,
            certificate_requests=certificate_request_service,
            users=user_service,
        ),
        prefix=settings.api_root,
    )
    app.include_router(health_router)
    install_exception_handlers(app)
    install_latency(app, settings)
    return app


app = create_app()
