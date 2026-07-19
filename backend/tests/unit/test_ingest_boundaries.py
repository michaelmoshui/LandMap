"""Unit tests for the pure transforms in the boundary ingestion script."""

from __future__ import annotations

import pytest
from shapely.geometry import Point, shape

from app.ingest.boundaries import (
    BURNABY_EXCLUDE_KEYWORDS,
    merge_geometries,
    municipality_features,
    neighborhood_features,
    simplify_points,
    simplify_ring,
    slugify,
)


def test_slugify() -> None:
    assert slugify("Port Coquitlam") == "port-coquitlam"
    assert slugify("Kensington-Cedar Cottage") == "kensington-cedar-cottage"
    assert slugify("  Electoral Area A ") == "electoral-area-a"


def test_simplify_points_drops_collinear_and_keeps_corners() -> None:
    line = [[0.0, 0.0], [1.0, 0.00001], [2.0, 0.0], [2.0, 2.0]]
    simplified = simplify_points(line, tolerance=0.001)
    assert simplified == [[0.0, 0.0], [2.0, 0.0], [2.0, 2.0]]

    # A point deviating beyond the tolerance survives.
    bent = [[0.0, 0.0], [1.0, 0.5], [2.0, 0.0]]
    assert simplify_points(bent, tolerance=0.001) == bent


def test_simplify_ring_preserves_closure_or_collapses() -> None:
    square = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
    simplified = simplify_ring(square, tolerance=0.001)
    assert simplified[0] == simplified[-1]
    assert len(simplified) >= 4

    sliver = [[0.0, 0.0], [1.0, 0.000001], [2.0, 0.0], [0.0, 0.0]]
    assert simplify_ring(sliver, tolerance=0.01) == []


def test_merge_geometries_combines_parts() -> None:
    poly_a = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    poly_b = {"type": "Polygon", "coordinates": [[[5, 5], [6, 5], [6, 6], [5, 5]]]}
    merged = merge_geometries([poly_a, poly_b])
    assert merged["type"] == "MultiPolygon"
    assert len(merged["coordinates"]) == 2
    assert merge_geometries([poly_a])["type"] == "Polygon"


def _square_geometry(offset: float = 0.0) -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [offset, 0.0],
                [offset + 0.01, 0.0],
                [offset + 0.01, 0.01],
                [offset, 0.01],
                [offset, 0.0],
            ]
        ],
    }


def test_municipality_features_merge_rows_by_name() -> None:
    raw = {
        "features": [
            {
                "properties": {"ShortName": "Delta", "FullName": "City of Delta"},
                "geometry": _square_geometry(0.0),
            },
            {
                "properties": {"ShortName": "Delta", "FullName": "City of Delta"},
                "geometry": _square_geometry(1.0),
            },
        ]
    }
    features = municipality_features(raw)
    assert len(features) == 1
    assert features[0]["properties"] == {
        "id": "muni-delta",
        "name": "Delta",
        "kind": "municipality",
    }
    assert features[0]["geometry"]["type"] == "MultiPolygon"


def _rect_geometry(minx: float, miny: float, maxx: float, maxy: float) -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]
        ],
    }


def test_municipality_features_excludes_electoral_area_a() -> None:
    raw = {
        "features": [
            {"properties": {"ShortName": "Electoral Area A"}, "geometry": _square_geometry(0.0)},
            {"properties": {"ShortName": "Vancouver"}, "geometry": _square_geometry(1.0)},
        ]
    }
    names = [f["properties"]["name"] for f in municipality_features(raw)]
    assert names == ["Vancouver"]


def test_municipality_features_carves_first_nation_out_of_overlapping_city() -> None:
    # A First Nation whose treaty lands sit inside a municipality (as Tsawwassen
    # does inside Delta) must be subtracted from that municipality: both stay
    # selectable, but they no longer both claim the same area.
    raw = {
        "features": [
            {"properties": {"ShortName": "Delta"}, "geometry": _rect_geometry(0.0, 0.0, 2.0, 2.0)},
            {
                "properties": {"ShortName": "Tsawwassen First Nation"},
                "geometry": _rect_geometry(0.0, 0.0, 1.0, 1.0),
            },
        ]
    }
    features = {f["properties"]["name"]: f for f in municipality_features(raw)}
    assert set(features) == {"Delta", "Tsawwassen First Nation"}

    delta = shape(features["Delta"]["geometry"])
    tfn = shape(features["Tsawwassen First Nation"]["geometry"])
    assert delta.intersection(tfn).area == pytest.approx(0.0, abs=1e-6)
    # The overlap corner now belongs only to the First Nation.
    assert tfn.contains(Point(0.5, 0.5))
    assert not delta.contains(Point(0.5, 0.5))


def test_neighborhood_features_are_namespaced_by_municipality() -> None:
    raw = {"features": [{"properties": {"name": "Kerrisdale"}, "geometry": _square_geometry()}]}
    features = neighborhood_features(raw, "name", "Vancouver")
    assert features[0]["properties"] == {
        "id": "hood-vancouver-kerrisdale",
        "name": "Kerrisdale (Vancouver)",
        "kind": "neighborhood",
    }


def test_neighborhood_features_exclude_non_neighborhood_plan_areas() -> None:
    raw = {
        "features": [
            {"properties": {"AREA_NAME": "Lougheed"}, "geometry": _square_geometry(0.0)},
            {"properties": {"AREA_NAME": "Chevron Buffer Area"}, "geometry": _square_geometry(1.0)},
            {"properties": {"AREA_NAME": "Burnaby Lake Park"}, "geometry": _square_geometry(2.0)},
        ]
    }
    features = neighborhood_features(
        raw, "AREA_NAME", "Burnaby", exclude_keywords=BURNABY_EXCLUDE_KEYWORDS
    )
    assert [f["properties"]["name"] for f in features] == ["Lougheed (Burnaby)"]
