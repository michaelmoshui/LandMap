"""API contract shared between backend and frontend.

Keep this stable. Changing it requires updating the frontend API client
(`frontend/src/api/`) and the e2e tests in the same change.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

LayerCategory = Literal["baseline", "planned"]


class LayerMeta(BaseModel):
    """Metadata describing a single map layer (not its geometry)."""

    id: str = Field(..., examples=["housing-prices"])
    title: str = Field(..., examples=["Housing Prices"])
    description: str = Field(default="")
    category: LayerCategory = Field(default="baseline")


class Feature(BaseModel):
    """A GeoJSON Feature."""

    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any] = Field(default_factory=dict)


class FeatureCollection(BaseModel):
    """A GeoJSON FeatureCollection returned for a layer."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Feature] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "landmap-backend"
    version: str
