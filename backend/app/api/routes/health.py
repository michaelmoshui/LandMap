"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.schemas.layers import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe used by containers, the proxy, and e2e tests."""
    return HealthResponse(version=__version__)
