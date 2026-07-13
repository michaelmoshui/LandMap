"""Layer registry and data access.

Currently returns hand-made sample data centered on the Greater Vancouver Area.
Replace the ``_sample_*`` builders with PostGIS-backed queries as real datasets
are ingested (see SKILL.md -> "Wire a layer to real PostGIS data").
"""

from __future__ import annotations

from collections.abc import Callable

from app.schemas.layers import Feature, FeatureCollection, LayerMeta

# --- Layer metadata registry ----------------------------------------------

_LAYERS: list[LayerMeta] = [
    LayerMeta(
        id="housing-prices",
        title="Housing Prices",
        description="Assessed/market housing values by area (sample data).",
        category="baseline",
    ),
    LayerMeta(
        id="demographics",
        title="Demographics",
        description="Population and household characteristics by area (sample data).",
        category="baseline",
    ),
    LayerMeta(
        id="skytrain-expansion",
        title="SkyTrain Expansion",
        description="Planned transit line extensions and new stations (sample data).",
        category="planned",
    ),
    LayerMeta(
        id="road-construction",
        title="Road Construction",
        description="Upcoming and active road/infrastructure projects (sample data).",
        category="planned",
    ),
    LayerMeta(
        id="new-highrises",
        title="New High-Rises",
        description="Approved and proposed high-rise developments (sample data).",
        category="planned",
    ),
]


def list_layers() -> list[LayerMeta]:
    """Return metadata for all available layers."""
    return list(_LAYERS)


def get_layer(layer_id: str) -> LayerMeta | None:
    """Return a single layer's metadata, or None if unknown."""
    return next((layer for layer in _LAYERS if layer.id == layer_id), None)


# --- Sample data builders --------------------------------------------------
# Coordinates are [lng, lat] (GeoJSON order) around Greater Vancouver.


def _point(lng: float, lat: float, **props: object) -> Feature:
    return Feature(geometry={"type": "Point", "coordinates": [lng, lat]}, properties=dict(props))


def _sample_housing_prices() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-123.1207, 49.2827, area="Downtown Vancouver", median_price=1150000),
            _point(-123.1139, 49.2606, area="Mount Pleasant", median_price=1420000),
            _point(-122.7969, 49.2057, area="Surrey Central", median_price=980000),
            _point(-122.9020, 49.2488, area="New Westminster", median_price=1050000),
            _point(-123.0000, 49.2500, area="Burnaby Metrotown", median_price=1230000),
        ]
    )


def _sample_demographics() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-123.1207, 49.2827, area="Downtown Vancouver", population=62000, density=18000),
            _point(-122.7969, 49.2057, area="Surrey Central", population=51000, density=6200),
            _point(-123.0000, 49.2500, area="Burnaby Metrotown", population=42000, density=9100),
        ]
    )


def _sample_skytrain_expansion() -> FeatureCollection:
    return FeatureCollection(
        features=[
            Feature(
                geometry={
                    "type": "LineString",
                    "coordinates": [
                        [-123.1139, 49.2606],
                        [-123.0800, 49.2600],
                        [-123.0460, 49.2490],
                    ],
                },
                properties={"project": "Broadway Subway (sample)", "status": "under-construction"},
            ),
            _point(-123.0800, 49.2600, station="Great Northern Way (sample)", opens="2027"),
        ]
    )


def _sample_road_construction() -> FeatureCollection:
    return FeatureCollection(
        features=[
            Feature(
                geometry={
                    "type": "LineString",
                    "coordinates": [[-122.9020, 49.2000], [-122.8500, 49.2100]],
                },
                properties={"project": "Pattullo Bridge Replacement (sample)", "status": "active"},
            ),
        ]
    )


def _sample_new_highrises() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-123.1180, 49.2830, name="Tower A (sample)", storeys=48, status="approved"),
            _point(
                -122.9990, 49.2495, name="Metrotown Tower (sample)", storeys=60, status="proposed"
            ),
        ]
    )


_BUILDERS: dict[str, Callable[[], FeatureCollection]] = {
    "housing-prices": _sample_housing_prices,
    "demographics": _sample_demographics,
    "skytrain-expansion": _sample_skytrain_expansion,
    "road-construction": _sample_road_construction,
    "new-highrises": _sample_new_highrises,
}


def get_features(layer_id: str) -> FeatureCollection | None:
    """Return the FeatureCollection for a layer, or None if unknown."""
    builder = _BUILDERS.get(layer_id)
    return builder() if builder else None
