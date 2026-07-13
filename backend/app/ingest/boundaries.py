"""Fetch real boundary polygons from government open-data portals.

Sources (all free, keyless; see SOURCES.md):
- Municipalities: Metro Vancouver Open Data, "Administrative Boundaries".
- Vancouver neighborhoods: City of Vancouver, "local-area-boundary".
- Burnaby neighborhoods: City of Burnaby, "Community Plan Area Boundaries".

Writes ``app/data/boundaries.geojson`` (committed to the repo), which
``app.services.boundaries`` serves at runtime. Geometry is Douglas-Peucker
simplified and coordinate-rounded so the file stays small. Idempotent:
re-running overwrites the file with fresh data.

Run inside the backend container:
    docker compose run --rm backend python -m app.ingest.boundaries

Lots are not ingested here: parcel polygons (ParcelMap BC) are a much larger
dataset and need PostGIS; the service keeps a few sample lots until then.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from typing import Any

MUNICIPALITIES_URL = (
    "https://services6.arcgis.com/56eqCzQ5SZhBaDST/arcgis/rest/services/"
    "Administrative_Boundaries/FeatureServer/10/query"
    "?where=1%3D1&outFields=FullName,ShortName&f=geojson&outSR=4326"
)
VANCOUVER_NEIGHBORHOODS_URL = (
    "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/"
    "local-area-boundary/exports/geojson"
)
BURNABY_NEIGHBORHOODS_URL = (
    "https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData1/MapServer/10/query"
    "?where=1%3D1&outFields=AREA_NAME&f=geojson&outSR=4326"
)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "boundaries.geojson"

# ~11 m at this latitude: invisible at neighborhood zoom, big size win.
SIMPLIFY_TOLERANCE_DEG = 0.0001
COORD_DECIMALS = 5

Position = list[float]


def slugify(name: str) -> str:
    """Lowercase, ASCII-ish, hyphen-separated id fragment."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _perpendicular_distance(point: Position, start: Position, end: Position) -> float:
    (px, py), (ax, ay), (bx, by) = point, start, end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def simplify_points(points: list[Position], tolerance: float) -> list[Position]:
    """Iterative Douglas-Peucker; endpoints are always kept."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        max_dist, index = 0.0, first
        for i in range(first + 1, last):
            dist = _perpendicular_distance(points[i], points[first], points[last])
            if dist > max_dist:
                max_dist, index = dist, i
        if max_dist > tolerance:
            keep[index] = True
            stack.append((first, index))
            stack.append((index, last))
    return [p for p, k in zip(points, keep, strict=True) if k]


def simplify_ring(ring: list[Position], tolerance: float) -> list[Position]:
    """Simplify a closed ring, preserving closure; degenerate rings collapse to []."""
    simplified = simplify_points(ring, tolerance)
    if len(simplified) < 4:  # a closed triangle needs 4 positions
        return []
    return simplified


def _round(position: Position) -> Position:
    return [round(c, COORD_DECIMALS) for c in position]


def simplify_polygon(coordinates: list[list[Position]], tolerance: float) -> list[list[Position]]:
    rings = []
    for ring in coordinates:
        simplified = simplify_ring(ring, tolerance)
        if simplified:
            rings.append([_round(p) for p in simplified])
    return rings


def simplify_geometry(geometry: dict[str, Any], tolerance: float) -> dict[str, Any] | None:
    """Simplify a Polygon/MultiPolygon; returns None if nothing survives."""
    if geometry["type"] == "Polygon":
        rings = simplify_polygon(geometry["coordinates"], tolerance)
        return {"type": "Polygon", "coordinates": rings} if rings else None
    if geometry["type"] == "MultiPolygon":
        polys = [simplify_polygon(poly, tolerance) for poly in geometry["coordinates"]]
        polys = [p for p in polys if p]
        if not polys:
            return None
        if len(polys) == 1:
            return {"type": "Polygon", "coordinates": polys[0]}
        return {"type": "MultiPolygon", "coordinates": polys}
    return None


def merge_geometries(geometries: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine Polygon/MultiPolygon geometries into one (Multi)Polygon."""
    parts: list[list[list[Position]]] = []
    for geometry in geometries:
        if geometry["type"] == "Polygon":
            parts.append(geometry["coordinates"])
        elif geometry["type"] == "MultiPolygon":
            parts.extend(geometry["coordinates"])
    if len(parts) == 1:
        return {"type": "Polygon", "coordinates": parts[0]}
    return {"type": "MultiPolygon", "coordinates": parts}


def _feature(id: str, name: str, kind: str, geometry: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {"id": id, "name": name, "kind": kind},
    }


def municipality_features(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Metro Vancouver rows -> one feature per municipality (rows merged by name)."""
    by_name: dict[str, list[dict[str, Any]]] = {}
    for feature in raw["features"]:
        props = feature["properties"]
        name = (props.get("ShortName") or props.get("FullName") or "").strip()
        if not name or feature.get("geometry") is None:
            continue
        by_name.setdefault(name, []).append(feature["geometry"])
    results = []
    for name, geometries in sorted(by_name.items()):
        merged = simplify_geometry(merge_geometries(geometries), SIMPLIFY_TOLERANCE_DEG)
        if merged:
            results.append(_feature(f"muni-{slugify(name)}", name, "municipality", merged))
    return results


def neighborhood_features(
    raw: dict[str, Any], name_key: str, municipality: str
) -> list[dict[str, Any]]:
    """City open-data rows -> neighborhood features named '<Area> (<City>)'."""
    results = []
    for feature in raw["features"]:
        name = (feature["properties"].get(name_key) or "").strip()
        if not name or feature.get("geometry") is None:
            continue
        simplified = simplify_geometry(feature["geometry"], SIMPLIFY_TOLERANCE_DEG)
        if not simplified:
            continue
        boundary_id = f"hood-{slugify(municipality)}-{slugify(name)}"
        results.append(
            _feature(boundary_id, f"{name} ({municipality})", "neighborhood", simplified)
        )
    results.sort(key=lambda f: f["properties"]["id"])
    return results


def _fetch_geojson(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 (fixed https URLs)
        return json.load(resp)


def main() -> None:
    print("Fetching municipalities (Metro Vancouver Open Data)...")
    munis = municipality_features(_fetch_geojson(MUNICIPALITIES_URL))
    print(f"  {len(munis)} municipalities")
    print("Fetching Vancouver neighborhoods (City of Vancouver Open Data)...")
    van = neighborhood_features(_fetch_geojson(VANCOUVER_NEIGHBORHOODS_URL), "name", "Vancouver")
    print(f"  {len(van)} neighborhoods")
    print("Fetching Burnaby neighborhoods (City of Burnaby Open Data)...")
    bby = neighborhood_features(_fetch_geojson(BURNABY_NEIGHBORHOODS_URL), "AREA_NAME", "Burnaby")
    print(f"  {len(bby)} neighborhoods")

    collection = {"type": "FeatureCollection", "features": munis + van + bby}
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as fh:
        json.dump(collection, fh, separators=(",", ":"))
        fh.write("\n")
    size_kb = DATA_PATH.stat().st_size // 1024
    print(f"Wrote {len(collection['features'])} boundaries to {DATA_PATH} ({size_kb} KB)")


if __name__ == "__main__":
    main()
