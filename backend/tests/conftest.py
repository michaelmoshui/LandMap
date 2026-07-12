"""Shared pytest fixtures for backend unit tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """A TestClient bound to a fresh app instance."""
    return TestClient(create_app())
