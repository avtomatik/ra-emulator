import asyncio

from fastapi import FastAPI, Request
from pydantic_settings import BaseSettings


def install_latency(app: FastAPI, settings: BaseSettings) -> None:
    @app.middleware("http")
    async def latency_middleware(request: Request, call_next):
        if settings.latency_ms > 0:
            await asyncio.sleep(settings.latency_ms / 1000)
        return await call_next(request)
