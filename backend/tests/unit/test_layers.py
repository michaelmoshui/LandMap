"""Unit tests for layer endpoints and the layer service."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services import layers as layers_service

EXPECTED_GVA_LAYER_IDS = {
    "housing-prices",
    "demographics",
    "skytrain-lines",
    "skytrain-stations",
    "bus-routes",
    "bus-stops",
    "seabus-wce",
    "skytrain-expansion",
    "road-construction",
    "new-highrises",
    "municipality-boundaries",
    "neighborhood-boundaries",
}

EXPECTED_GTA_LAYER_IDS = {
    "gta-housing-prices",
    "gta-demographics",
    "gta-subway-lines",
    "gta-subway-stations",
    "gta-streetcar-lines",
    "gta-bus-routes",
    "gta-bus-stops",
    "gta-go-transit",
    "gta-transit-expansion",
    "gta-road-construction",
    "gta-new-highrises",
}

EXPECTED_LAYER_IDS = EXPECTED_GVA_LAYER_IDS | EXPECTED_GTA_LAYER_IDS


def test_list_layers_returns_all(client: TestClient) -> None:
    resp = client.get("/api/layers")
    assert resp.status_code == 200
    ids = {layer["id"] for layer in resp.json()}
    assert ids == EXPECTED_LAYER_IDS


@pytest.mark.parametrize(
    ("region", "expected"),
    [("gva", EXPECTED_GVA_LAYER_IDS), ("gta", EXPECTED_GTA_LAYER_IDS)],
)
def test_list_layers_filters_by_region(client: TestClient, region: str, expected: set[str]) -> None:
    resp = client.get("/api/layers", params={"region": region})
    assert resp.status_code == 200
    layers = resp.json()
    assert {layer["id"] for layer in layers} == expected
    assert all(layer["region"] == region for layer in layers)


def test_list_layers_unknown_region_is_empty(client: TestClient) -> None:
    resp = client.get("/api/layers", params={"region": "nowhere"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_layer_metadata_has_required_fields(client: TestClient) -> None:
    resp = client.get("/api/layers")
    for layer in resp.json():
        assert layer["title"]
        assert layer["category"] in {"baseline", "planned"}
        assert layer["region"] in {"gva", "gta"}


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


# --- ingested snapshots ------------------------------------------------------


def _write_snapshot(data_dir: Path, layer_id: str, body: str) -> None:
    path = data_dir / "gva" / f"{layer_id}.geojson"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_snapshot_wins_over_sample_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-123.1, 49.28]},
                "properties": {"area": "Ingested Area"},
            }
        ],
    }
    _write_snapshot(tmp_path, "housing-prices", json.dumps(snapshot))
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))

    collection = layers_service.get_features("housing-prices")
    assert collection is not None
    assert len(collection.features) == 1
    assert collection.features[0].properties["area"] == "Ingested Area"


def test_invalid_snapshot_falls_back_to_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_snapshot(tmp_path, "housing-prices", "not geojson {")
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))

    collection = layers_service.get_features("housing-prices")
    assert collection is not None
    # Sample data has several points; the broken snapshot is ignored.
    assert len(collection.features) >= 2


def test_missing_snapshot_serves_sample(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    collection = layers_service.get_features("skytrain-expansion")
    assert collection is not None
    assert len(collection.features) >= 1
