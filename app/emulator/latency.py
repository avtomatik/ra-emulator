"""Optional fault injection for contract-testing clients (never affects health checks)."""

import asyncio
import random

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.settings import Settings


def install_latency(app: FastAPI, settings: Settings) -> None:
    @app.middleware("http")
    async def emulator_behavior(request: Request, call_next):
        if request.url.path.startswith(settings.api_root + "/"):
            if settings.latency_ms:
                await asyncio.sleep(settings.latency_ms / 1000)
            if (
                settings.failure_rate
                and random.random() < settings.failure_rate
            ):
                return JSONResponse(
                    status_code=settings.failure_status,
                    content={
                        "error": "SIMULATED_RA_FAILURE",
                        "message": "Injected RA failure",
                    },
                )
        return await call_next(request)
