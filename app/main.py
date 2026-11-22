"""FastAPI composition root; no globals for request-scoped database connections."""

from fastapi import FastAPI

from app.application.certificate_requests import CertificateRequestService
from app.application.certificates import CertificateService
from app.application.revocation_requests import RevocationRequestService
from app.application.users import UserService
from app.config.settings import Settings, get_settings
from app.dataset.ensure import ensure_dataset_exists
from app.emulator.errors import install_exception_handlers
from app.emulator.latency import install_latency
from app.interfaces.health import router as health_router
from app.interfaces.routes import build_router
from app.repositories.certificate import CertificateRepository
from app.repositories.certificate_request import CertificateRequestRepository
from app.repositories.revocation_request import RevocationRequestRepository
from app.repositories.user import UserRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else get_settings()
    store = ensure_dataset_exists(settings)
    app = FastAPI(title="RA Contract Emulator", version="1.1.0")
    app.state.store = store
    app.include_router(
        build_router(
            certificates=CertificateService(
                CertificateRepository(store), api_root=settings.api_root
            ),
            certificate_requests=CertificateRequestService(
                CertificateRequestRepository(store), api_root=settings.api_root
            ),
            users=UserService(
                UserRepository(store), api_root=settings.api_root
            ),
            revocation_requests=RevocationRequestService(
                RevocationRequestRepository(store), api_root=settings.api_root
            ),
        ),
        prefix=settings.api_root,
    )
    app.include_router(health_router)
    install_exception_handlers(app)
    install_latency(app, settings)
    return app


app = create_app()
