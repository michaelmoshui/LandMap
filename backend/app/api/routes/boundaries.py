"""Boundary search and geometry endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.boundaries import BoundarySummary
from app.schemas.layers import Feature
from app.services import boundaries as boundaries_service

router = APIRouter(prefix="/boundaries", tags=["boundaries"])


@router.get("/search", response_model=list[BoundarySummary])
def search_boundaries(q: str = Query(default="", max_length=100)) -> list[BoundarySummary]:
    """Search municipalities, neighborhoods, and lots by name."""
    return boundaries_service.search_boundaries(q)


@router.get("/{boundary_id}", response_model=Feature)
def boundary_feature(boundary_id: str) -> Feature:
    """Return the GeoJSON Feature (polygon) for a boundary."""
    feature = boundaries_service.get_boundary(boundary_id)
    if feature is None:
        raise HTTPException(status_code=404, detail=f"Unknown boundary: {boundary_id}")
    return feature
