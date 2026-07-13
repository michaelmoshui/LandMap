"""Unit tests for layer endpoints and the layer service."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services import layers as layers_service

EXPECTED_LAYER_IDS = {
    "housing-prices",
    "demographics",
    "skytrain-expansion",
    "road-construction",
    "new-highrises",
    "municipality-boundaries",
    "neighborhood-boundaries",
}


def test_list_layers_returns_all(client: TestClient) -> None:
    resp = client.get("/api/layers")
    assert resp.status_code == 200
    ids = {layer["id"] for layer in resp.json()}
    assert ids == EXPECTED_LAYER_IDS


def test_layer_metadata_has_required_fields(client: TestClient) -> None:
    resp = client.get("/api/layers")
    for layer in resp.json():
        assert layer["title"]
        assert layer["category"] in {"baseline", "planned"}


@pytest.mark.parametrize("layer_id", sorted(EXPECTED_LAYER_IDS))
def test_features_return_valid_geojson(client: TestClient, layer_id: str) -> None:
    resp = client.get(f"/api/layers/{layer_id}/features")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "FeatureCollection"
    assert isinstance(body["features"], list)
    assert len(body["features"]) >= 1
    for feature in body["features"]:
        assert feature["type"] == "Feature"
        assert "coordinates" in feature["geometry"]


def test_boundary_layers_expose_all_ingested_boundaries(client: TestClient) -> None:
    resp = client.get("/api/layers/municipality-boundaries/features")
    munis = resp.json()["features"]
    muni_ids = {f["properties"]["id"] for f in munis}
    assert "muni-coquitlam" in muni_ids
    assert len(muni_ids) >= 20
    assert all(f["properties"]["kind"] == "municipality" for f in munis)

    resp = client.get("/api/layers/neighborhood-boundaries/features")
    hoods = resp.json()["features"]
    hood_ids = {f["properties"]["id"] for f in hoods}
    assert {"hood-vancouver-kerrisdale", "hood-burnaby-lougheed"} <= hood_ids
    assert all(f["properties"]["kind"] == "neighborhood" for f in hoods)


def test_unknown_layer_returns_404(client: TestClient) -> None:
    resp = client.get("/api/layers/does-not-exist/features")
    assert resp.status_code == 404


def test_service_get_layer_roundtrip() -> None:
    for meta in layers_service.list_layers():
        assert layers_service.get_layer(meta.id) is not None
        assert layers_service.get_features(meta.id) is not None
    assert layers_service.get_layer("nope") is None
    assert layers_service.get_features("nope") is None
