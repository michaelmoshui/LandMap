"""Unit tests for the SOURCES.md catalog (regions + data sources)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services import sources as sources_service
from app.services.sources import parse_sources_md

SAMPLE_MD = """\
# Catalog

## Greater Toronto Area (GTA)

### Toronto Core
*   **City of Toronto Portal**
    *   **Description**: The main portal.
    *   **Endpoint**: [Toronto Portal](https://toronto.example.com)

## Greater Vancouver Area (GVA) / Lower Mainland

### Regional Hubs
*   **Metro Vancouver Portal**
    *   **Description**: Regional hub.
    *   **Endpoint**: [Metro Van](https://vancouver.example.com/data)
*   **Broken Entry Without Endpoint**
    *   **Description**: Should be skipped.

## Programmatic Access Protocols

*   **Protocol Type**: `ArcGIS FeatureServer` notes that are not a source.
"""


# --- Parser -----------------------------------------------------------------


def test_parse_regions_from_headings() -> None:
    regions, _ = parse_sources_md(SAMPLE_MD)
    assert [r.id for r in regions] == ["gta", "gva"]
    assert regions[0].title == "Greater Toronto Area"
    assert regions[1].title == "Greater Vancouver Area"


def test_parse_regions_have_viewports() -> None:
    regions, _ = parse_sources_md(SAMPLE_MD)
    gva = next(r for r in regions if r.id == "gva")
    assert gva.center[0] == pytest.approx(-123.02)
    assert gva.zoom > 0


def test_parse_sources_fields() -> None:
    _, sources = parse_sources_md(SAMPLE_MD)
    toronto = next(s for s in sources if s.region == "gta")
    assert toronto.name == "City of Toronto Portal"
    assert toronto.url == "https://toronto.example.com"
    assert toronto.description == "The main portal."
    assert toronto.group == "Toronto Core"
    assert toronto.id == "city-of-toronto-portal"


def test_parse_skips_incomplete_entries_and_prose_sections() -> None:
    regions, sources = parse_sources_md(SAMPLE_MD)
    names = {s.name for s in sources}
    assert "Broken Entry Without Endpoint" not in names
    assert all(r.id != "programmatic-access-protocols" for r in regions)


def test_parse_empty_text_yields_nothing() -> None:
    regions, sources = parse_sources_md("")
    assert regions == []
    assert sources == []


# --- Service (real SOURCES.md when mounted, fallback otherwise) -------------


def test_list_regions_includes_gva_and_gta() -> None:
    ids = {r.id for r in sources_service.list_regions()}
    assert {"gva", "gta"} <= ids


def test_missing_sources_file_falls_back_to_default_regions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "sources_path", "/nonexistent/SOURCES.md")
    ids = {r.id for r in sources_service.list_regions()}
    assert {"gva", "gta"} <= ids
    assert sources_service.list_sources() == []


# --- API --------------------------------------------------------------------


def test_regions_endpoint(client: TestClient) -> None:
    resp = client.get("/api/regions")
    assert resp.status_code == 200
    regions = resp.json()
    ids = {r["id"] for r in regions}
    assert {"gva", "gta"} <= ids
    for region in regions:
        assert region["title"]
        assert len(region["center"]) == 2


def test_sources_endpoint_filters_by_region(client: TestClient) -> None:
    resp = client.get("/api/sources", params={"region": "gva"})
    assert resp.status_code == 200
    assert all(s["region"] == "gva" for s in resp.json())


def test_sources_endpoint_unknown_region_is_empty(client: TestClient) -> None:
    resp = client.get("/api/sources", params={"region": "nowhere"})
    assert resp.status_code == 200
    assert resp.json() == []
