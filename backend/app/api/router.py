"""Aggregate API router. Include new route modules here."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import boundaries, health, layers

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(layers.router)
api_router.include_router(boundaries.router)
