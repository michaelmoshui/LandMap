"""Layer registry and data access.

Layers are grouped by region (see ``app.services.sources`` for the region
catalog parsed from SOURCES.md). Currently returns hand-made sample data for
the Greater Vancouver Area (``gva``) and Greater Toronto Area (``gta``).
Replace the ``_sample_*`` builders with PostGIS-backed queries as real datasets
are ingested from the portals in SOURCES.md (see SKILL.md -> "Wire a layer to
real PostGIS data").
"""

from __future__ import annotations

from collections.abc import Callable

from app.schemas.layers import Feature, FeatureCollection, LayerMeta

# --- Layer metadata registry ----------------------------------------------

_LAYERS: list[LayerMeta] = [
    # Greater Vancouver Area
    LayerMeta(
        id="housing-prices",
        title="Housing Prices",
        description="Assessed/market housing values by area (sample data).",
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="demographics",
        title="Demographics",
        description="Population and household characteristics by area (sample data).",
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="skytrain-expansion",
        title="SkyTrain Expansion",
        description="Planned transit line extensions and new stations (sample data).",
        category="planned",
        region="gva",
    ),
    LayerMeta(
        id="road-construction",
        title="Road Construction",
        description="Upcoming and active road/infrastructure projects (sample data).",
        category="planned",
        region="gva",
    ),
    LayerMeta(
        id="new-highrises",
        title="New High-Rises",
        description="Approved and proposed high-rise developments (sample data).",
        category="planned",
        region="gva",
    ),
    # Greater Toronto Area
    LayerMeta(
        id="gta-housing-prices",
        title="Housing Prices",
        description="Assessed/market housing values by area (sample data).",
        category="baseline",
        region="gta",
    ),
    LayerMeta(
        id="gta-demographics",
        title="Demographics",
        description="Population and household characteristics by area (sample data).",
        category="baseline",
        region="gta",
    ),
    LayerMeta(
        id="gta-transit-expansion",
        title="Transit Expansion",
        description="Planned subway/transit extensions and new stations (sample data).",
        category="planned",
        region="gta",
    ),
    LayerMeta(
        id="gta-road-construction",
        title="Road Construction",
        description="Upcoming and active road/infrastructure projects (sample data).",
        category="planned",
        region="gta",
    ),
    LayerMeta(
        id="gta-new-highrises",
        title="New High-Rises",
        description="Approved and proposed high-rise developments (sample data).",
        category="planned",
        region="gta",
    ),
]


def list_layers(region: str | None = None) -> list[LayerMeta]:
    """Return metadata for all layers, optionally filtered to one region."""
    if region is None:
        return list(_LAYERS)
    return [layer for layer in _LAYERS if layer.region == region]


def get_layer(layer_id: str) -> LayerMeta | None:
    """Return a single layer's metadata, or None if unknown."""
    return next((layer for layer in _LAYERS if layer.id == layer_id), None)


# --- Sample data builders --------------------------------------------------
# Coordinates are [lng, lat] (GeoJSON order).


def _point(lng: float, lat: float, **props: object) -> Feature:
    return Feature(geometry={"type": "Point", "coordinates": [lng, lat]}, properties=dict(props))


# Greater Vancouver Area samples


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
            _point(-122.9990, 49.2495, name="Metrotown (sample)", storeys=60, status="proposed"),
        ]
    )


# Greater Toronto Area samples


def _sample_gta_housing_prices() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-79.3832, 43.6532, area="Downtown Toronto", median_price=950000),
            _point(-79.4113, 43.7615, area="North York Centre", median_price=1050000),
            _point(-79.2578, 43.7764, area="Scarborough Centre", median_price=890000),
            _point(-79.6441, 43.5890, area="Mississauga City Centre", median_price=1010000),
            _point(-79.5085, 43.8361, area="Vaughan Metropolitan Centre", median_price=1240000),
        ]
    )


def _sample_gta_demographics() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-79.3832, 43.6532, area="Downtown Toronto", population=275000, density=16000),
            _point(-79.4113, 43.7615, area="North York Centre", population=105000, density=7100),
            _point(-79.6441, 43.5890, area="Mississauga Centre", population=92000, density=4400),
        ]
    )


def _sample_gta_transit_expansion() -> FeatureCollection:
    return FeatureCollection(
        features=[
            Feature(
                geometry={
                    "type": "LineString",
                    "coordinates": [
                        [-79.4096, 43.6355],
                        [-79.3961, 43.6486],
                        [-79.3792, 43.6524],
                        [-79.3600, 43.6531],
                        [-79.3435, 43.6570],
                        [-79.3450, 43.6780],
                        [-79.3390, 43.7165],
                    ],
                },
                properties={"project": "Ontario Line (sample)", "status": "under-construction"},
            ),
            _point(-79.3435, 43.6570, station="East Harbour (sample)", opens="2031"),
        ]
    )


def _sample_gta_road_construction() -> FeatureCollection:
    return FeatureCollection(
        features=[
            Feature(
                geometry={
                    "type": "LineString",
                    "coordinates": [
                        [-79.4046, 43.6363],
                        [-79.3900, 43.6398],
                        [-79.3762, 43.6413],
                    ],
                },
                properties={
                    "project": "Gardiner Expressway Rehabilitation (sample)",
                    "status": "active",
                },
            ),
        ]
    )


def _sample_gta_new_highrises() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-79.3872, 43.6702, name="The One (sample)", storeys=85, status="approved"),
            _point(-79.3735, 43.6427, name="SkyTower (sample)", storeys=105, status="approved"),
            _point(-79.3860, 43.6440, name="Union Park (sample)", storeys=58, status="proposed"),
        ]
    )


_BUILDERS: dict[str, Callable[[], FeatureCollection]] = {
    "housing-prices": _sample_housing_prices,
    "demographics": _sample_demographics,
    "skytrain-expansion": _sample_skytrain_expansion,
    "road-construction": _sample_road_construction,
    "new-highrises": _sample_new_highrises,
    "gta-housing-prices": _sample_gta_housing_prices,
    "gta-demographics": _sample_gta_demographics,
    "gta-transit-expansion": _sample_gta_transit_expansion,
    "gta-road-construction": _sample_gta_road_construction,
    "gta-new-highrises": _sample_gta_new_highrises,
}


def get_features(layer_id: str) -> FeatureCollection | None:
    """Return the FeatureCollection for a layer, or None if unknown."""
    builder = _BUILDERS.get(layer_id)
    return builder() if builder else None
