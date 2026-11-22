from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.config.paths import BASE_DIR


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RADP_EMULATOR_", env_file=".env", extra="ignore"
    )
    api_root: str = "/api/ra"
    database_path: Path = BASE_DIR / "data" / "emulator.sqlite3"
    latency_ms: Annotated[int, Field(ge=0)] = 0
    failure_rate: Annotated[float, Field(ge=0, le=1)] = 0.0
    failure_status: Annotated[int, Field(ge=400, le=599)] = 503
    certificate_folders: Annotated[tuple[str, ...], NoDecode] = ("default",)

    @field_validator("certificate_folders", mode="before")
    @classmethod
    def parse_certificate_folders(cls, value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            values = value.split(",")
        elif isinstance(value, (list, tuple)):
            values = value
        else:
            raise ValueError(
                "Certificate folders must be a CSV string or sequence"
            )
        if not values or any(
            not isinstance(v, str) or not v.strip() for v in values
        ):
            raise ValueError(
                "Certificate folders must contain non-empty names"
            )
        return tuple(dict.fromkeys(v.strip() for v in values))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide cached settings; explicit Settings(...) remains testable."""
    return Settings()
