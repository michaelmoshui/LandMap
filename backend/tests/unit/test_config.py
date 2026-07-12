"""Unit tests for settings parsing (regression guard for CORS env handling)."""

from __future__ import annotations

from app.core.config import Settings


def test_cors_origins_parsed_from_comma_string(monkeypatch) -> None:
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "http://a.com,http://b.com")
    settings = Settings()
    assert settings.backend_cors_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_default_is_list() -> None:
    settings = Settings(_env_file=None)
    assert isinstance(settings.backend_cors_origins, list)


def test_database_url_built_from_parts() -> None:
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.postgres_db in settings.database_url
