"""Map layer endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.layers import FeatureCollection, LayerMeta
from app.services import layers as layers_service

router = APIRouter(prefix="/layers", tags=["layers"])


@router.get("", response_model=list[LayerMeta])
def list_layers(region: str | None = None) -> list[LayerMeta]:
    """List available map layers, optionally filtered to one region."""
    return layers_service.list_layers(region)


@router.get("/{layer_id}/features", response_model=FeatureCollection)
def layer_features(layer_id: str) -> FeatureCollection:
    """Return the GeoJSON FeatureCollection for a given layer."""
    if layers_service.get_layer(layer_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown layer: {layer_id}")
    features = layers_service.get_features(layer_id)
    if features is None:
        raise HTTPException(status_code=404, detail=f"No data for layer: {layer_id}")
    return features
