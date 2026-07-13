"""Unit tests for boundary search endpoints and the boundary service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services import boundaries as boundaries_service


def test_search_matches_all_three_kinds(client: TestClient) -> None:
    cases = {
        "coquitlam": ("muni-coquitlam", "municipality"),
        "kerrisdale": ("hood-vancouver-kerrisdale", "neighborhood"),
        "lougheed": ("hood-burnaby-lougheed", "neighborhood"),
        "kingsway": ("lot-015-632-880", "lot"),
    }
    for query, (expected_id, expected_kind) in cases.items():
        resp = client.get("/api/boundaries/search", params={"q": query})
        assert resp.status_code == 200
        results = resp.json()
        match = next((r for r in results if r["id"] == expected_id), None)
        assert match is not None, f"query {query!r} should return {expected_id}"
        assert match["kind"] == expected_kind
        assert match["name"]


def test_search_covers_all_metro_vancouver_municipalities() -> None:
    for name in ["Vancouver", "Burnaby", "Richmond", "Surrey", "Coquitlam", "Delta"]:
        results = boundaries_service.search_boundaries(name)
        assert any(r.kind == "municipality" and name in r.name for r in results), name


def test_search_is_case_insensitive_and_substring() -> None:
    assert boundaries_service.search_boundaries("KERRIS")
    assert boundaries_service.search_boundaries("mount") == boundaries_service.search_boundaries(
        "MOUNT"
    )


def test_search_orders_broadest_kind_first() -> None:
    results = boundaries_service.search_boundaries("o")
    kinds = [r.kind for r in results]
    order = {"municipality": 0, "neighborhood": 1, "lot": 2}
    assert kinds == sorted(kinds, key=lambda k: order[k])


def test_search_caps_results() -> None:
    # "a" matches most names; the response must stay bounded.
    assert len(boundaries_service.search_boundaries("a")) <= 20


def test_blank_query_returns_no_results(client: TestClient) -> None:
    assert boundaries_service.search_boundaries("   ") == []
    resp = client.get("/api/boundaries/search")
    assert resp.status_code == 200
    assert resp.json() == []


def test_boundary_feature_is_valid_polygon(client: TestClient) -> None:
    resp = client.get("/api/boundaries/hood-vancouver-kitsilano")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "Feature"
    assert body["geometry"]["type"] in {"Polygon", "MultiPolygon"}
    ring = body["geometry"]["coordinates"][0]
    if body["geometry"]["type"] == "MultiPolygon":
        ring = ring[0]
    assert len(ring) >= 4
    assert ring[0] == ring[-1]
    assert body["properties"] == {
        "id": "hood-vancouver-kitsilano",
        "name": "Kitsilano (Vancouver)",
        "kind": "neighborhood",
    }


def test_municipality_shape_is_not_a_rectangle(client: TestClient) -> None:
    # Real ingested outlines must follow the actual municipal boundary.
    resp = client.get("/api/boundaries/muni-coquitlam")
    assert resp.status_code == 200
    geometry = resp.json()["geometry"]
    ring = geometry["coordinates"][0]
    if geometry["type"] == "MultiPolygon":
        ring = ring[0]
    assert len(ring) > 20


def test_every_search_result_has_fetchable_geometry() -> None:
    for summary in boundaries_service.search_boundaries("o"):
        assert boundaries_service.get_boundary(summary.id) is not None


def test_unknown_boundary_returns_404(client: TestClient) -> None:
    resp = client.get("/api/boundaries/does-not-exist")
    assert resp.status_code == 404
