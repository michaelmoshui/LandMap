"""Boundary registry and search: municipalities, neighborhoods, and lots.

Municipalities and neighborhoods are real government open-data polygons,
ingested into ``app/data/boundaries.geojson`` by ``app.ingest.boundaries``
(run it to refresh; sources are listed there and in SOURCES.md).

Lots are still hand-made samples: real parcel polygons (ParcelMap BC) are a
much larger dataset that needs the PostGIS-backed path (see SKILL.md).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.schemas.boundaries import BoundaryKind, BoundarySummary
from app.schemas.layers import Feature

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "boundaries.geojson"

_MAX_RESULTS = 20

# Listing order for search results: broadest first.
_KIND_ORDER: dict[BoundaryKind, int] = {"municipality": 0, "neighborhood": 1, "lot": 2}


def _rect(min_lng: float, min_lat: float, max_lng: float, max_lat: float) -> dict[str, object]:
    """A rectangular GeoJSON Polygon - good enough for sample lots."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [min_lng, min_lat],
                [max_lng, min_lat],
                [max_lng, max_lat],
                [min_lng, max_lat],
                [min_lng, min_lat],
            ]
        ],
    }


class _Boundary:
    def __init__(self, id: str, name: str, kind: BoundaryKind, geometry: dict[str, object]) -> None:
        self.id = id
        self.name = name
        self.kind = kind
        self.geometry = geometry

    def summary(self) -> BoundarySummary:
        return BoundarySummary(id=self.id, name=self.name, kind=self.kind)

    def feature(self) -> Feature:
        return Feature(
            geometry=self.geometry,
            properties={"id": self.id, "name": self.name, "kind": self.kind},
        )


# Sample parcels (named by PID + civic address) until ParcelMap BC is wired in.
_SAMPLE_LOTS: list[_Boundary] = [
    _Boundary(
        "lot-007-241-374",
        "Lot 007-241-374 (2131 W 4th Ave)",
        "lot",
        _rect(-123.1566, 49.2678, -123.1560, 49.2682),
    ),
    _Boundary(
        "lot-015-632-880",
        "Lot 015-632-880 (4700 Kingsway)",
        "lot",
        _rect(-123.0016, 49.2278, -123.0008, 49.2284),
    ),
    _Boundary(
        "lot-024-118-556",
        "Lot 024-118-556 (128 W Cordova St)",
        "lot",
        _rect(-123.1066, 49.2830, -123.1058, 49.2836),
    ),
]

_VALID_KINDS = set(_KIND_ORDER)


@lru_cache(maxsize=1)
def _boundaries() -> list[_Boundary]:
    """All boundaries: ingested municipalities/neighborhoods plus sample lots."""
    with _DATA_PATH.open(encoding="utf-8") as fh:
        collection = json.load(fh)
    loaded = [
        _Boundary(props["id"], props["name"], props["kind"], feature["geometry"])
        for feature in collection["features"]
        if (props := feature["properties"])["kind"] in _VALID_KINDS
    ]
    return loaded + _SAMPLE_LOTS


@lru_cache(maxsize=1)
def _boundaries_by_id() -> dict[str, _Boundary]:
    return {b.id: b for b in _boundaries()}


def search_boundaries(query: str) -> list[BoundarySummary]:
    """Case-insensitive substring search across all boundary names."""
    needle = query.strip().lower()
    if not needle:
        return []
    matches = [b for b in _boundaries() if needle in b.name.lower()]
    matches.sort(key=lambda b: (_KIND_ORDER[b.kind], b.name))
    return [b.summary() for b in matches[:_MAX_RESULTS]]


def get_boundary(boundary_id: str) -> Feature | None:
    """Return a boundary's GeoJSON Feature, or None if unknown."""
    boundary = _boundaries_by_id().get(boundary_id)
    return boundary.feature() if boundary else None
