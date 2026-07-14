"""Application configuration, loaded from environment variables."""

from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Values come from the environment with safe defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LandMap API"
    api_prefix: str = "/api"
    log_level: str = "info"

    # Path to the SOURCES.md catalog of regions/data portals. The compose files
    # bind-mount the repo's SOURCES.md to /app/SOURCES.md (the workdir).
    sources_path: str = "SOURCES.md"

    # Directory holding ingested GeoJSON snapshots (<data_dir>/<region>/<layer>.geojson).
    # Relative to the workdir: resolves to backend/app/data on the host and
    # /app/app/data in the container; `app.ingest.*` writes here too.
    data_dir: str = "app/data"

    # CORS: comma-separated origins, e.g. "http://localhost,http://localhost:5173".
    # NoDecode stops pydantic-settings from JSON-parsing the env value so our
    # validator below can split the plain comma-separated string.
    backend_cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost",
        "http://localhost:5173",
    ]

    # Database (PostGIS). Optional at this stage: endpoints serve sample data.
    postgres_user: str = "landmap"
    postgres_password: str = "landmap"
    postgres_db: str = "landmap"
    postgres_host: str = "db"
    postgres_port: int = 5432

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
