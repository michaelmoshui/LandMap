"""Region and data-source endpoints, backed by the SOURCES.md catalog."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.layers import DataSource, RegionMeta
from app.services import sources as sources_service

router = APIRouter(tags=["regions"])


@router.get("/regions", response_model=list[RegionMeta])
def list_regions() -> list[RegionMeta]:
    """List the metro regions the map covers, with their viewports."""
    return sources_service.list_regions()


@router.get("/sources", response_model=list[DataSource])
def list_sources(region: str | None = None) -> list[DataSource]:
    """List open-data portals from SOURCES.md, optionally for one region."""
    return sources_service.list_sources(region)
