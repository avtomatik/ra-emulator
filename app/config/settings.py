from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RADP_EMULATOR_", env_file=".env", extra="ignore"
    )
    api_root: str = "/api/ra"
    latency_ms: Annotated[int, Field(ge=0)] = 0
    failure_rate: Annotated[float, Field(ge=0, le=1)] = 0.0
    failure_status: Annotated[int, Field(ge=400, le=599)] = 503
