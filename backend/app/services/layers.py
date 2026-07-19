"""Layer registry and data access.

Layers are grouped by region (see ``app.services.sources`` for the region
catalog parsed from SOURCES.md). Feature data comes from GeoJSON snapshots
under ``settings.data_dir`` (written by the ``app.ingest.*`` scripts pulling
from the portals in SOURCES.md); layers without a snapshot fall back to the
hand-made ``_sample_*`` builders so the app keeps working before ingestion
has run. Move hot layers into PostGIS-backed queries as they outgrow flat
files (see SKILL.md -> "Wire a layer to real PostGIS data").
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.layers import Feature, FeatureCollection, LayerMeta
from app.services import boundaries as boundaries_service

logger = logging.getLogger(__name__)

# --- Layer metadata registry ----------------------------------------------

_LAYERS: list[LayerMeta] = [
    # Greater Vancouver Area
    LayerMeta(
        id="housing-prices",
        title="Housing Prices",
        description=(
            "Average assessed property values by Vancouver local area, split into "
            "strata (condo) and land parcels. Source: City of Vancouver property "
            "tax report."
        ),
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="demographics",
        title="Demographics",
        description=(
            "2021 Census population, dwellings, and density by Metro Vancouver "
            "municipality. Source: Statistics Canada."
        ),
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="skytrain-lines",
        title="SkyTrain Lines",
        description=(
            "SkyTrain routes (Expo, Millennium and Canada Line) in TransLink's "
            "official line colours. Source: TransLink GTFS static feed."
        ),
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="skytrain-stations",
        title="SkyTrain Stations",
        description=(
            "SkyTrain stations with the lines serving each. Source: TransLink GTFS static feed."
        ),
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="bus-routes",
        title="Bus Routes",
        description=(
            "All TransLink bus routes in TransLink's colours (RapidBus green, "
            "99 B-Line orange, local routes gray-blue). "
            "Source: TransLink GTFS static feed."
        ),
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="bus-stops",
        title="Bus Stops",
        description=(
            "Every TransLink bus stop with the routes serving it. "
            "Source: TransLink GTFS static feed."
        ),
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="seabus-wce",
        title="SeaBus & West Coast Express",
        description=(
            "SeaBus and West Coast Express routes and stations in TransLink's "
            "official colours. Source: TransLink GTFS static feed."
        ),
        category="baseline",
        region="gva",
    ),
    LayerMeta(
        id="skytrain-expansion",
        title="SkyTrain Expansion",
        description=(
            "SkyTrain lines under construction (Broadway Extension, Surrey-Langley) "
            "and their future stations. Source: OpenStreetMap contributors (ODbL)."
        ),
        category="planned",
        region="gva",
    ),
    LayerMeta(
        id="road-construction",
        title="Road Construction",
        description=(
            "Road projects under construction and upcoming in Vancouver. "
            "Source: City of Vancouver Road Ahead."
        ),
        category="planned",
        region="gva",
    ),
    LayerMeta(
        id="new-highrises",
        title="New High-Rises",
        description=(
            "New residential buildings worth $20M+ with permits issued since 2023. "
            "Source: City of Vancouver issued building permits."
        ),
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
        id="gta-subway-lines",
        title="Subway Lines",
        description=(
            "TTC rapid transit Lines 1-6 (subway and LRT) in the TTC's "
            "official line colours. Source: TTC GTFS static feed."
        ),
        category="baseline",
        region="gta",
    ),
    LayerMeta(
        id="gta-subway-stations",
        title="Subway Stations",
        description=(
            "TTC subway and LRT stations with the lines serving each. "
            "Source: TTC GTFS static feed."
        ),
        category="baseline",
        region="gta",
    ),
    LayerMeta(
        id="gta-streetcar-lines",
        title="Streetcar Lines",
        description=(
            "TTC streetcar network in the TTC's colours (day routes red, "
            "night routes blue). Source: TTC GTFS static feed."
        ),
        category="baseline",
        region="gta",
    ),
    LayerMeta(
        id="gta-bus-routes",
        title="Bus Routes",
        description=(
            "All TTC bus routes in the TTC's colours (day red, express green, "
            "night blue). Source: TTC GTFS static feed."
        ),
        category="baseline",
        region="gta",
    ),
    LayerMeta(
        id="gta-bus-stops",
        title="Bus Stops",
        description=(
            "Every TTC bus and streetcar stop with the routes serving it. "
            "Source: TTC GTFS static feed."
        ),
        category="baseline",
        region="gta",
    ),
    LayerMeta(
        id="gta-go-transit",
        title="GO Transit Rail",
        description=(
            "GO train lines and stations in Metrolinx's official line "
            "colours. Source: GO Transit (Metrolinx) GTFS static feed."
        ),
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
    LayerMeta(
        id="municipality-boundaries",
        title="Municipality Boundaries",
        description="Metro Vancouver municipal boundaries (open data). Click one to focus it.",
        category="baseline",
    ),
    LayerMeta(
        id="neighborhood-boundaries",
        title="Neighborhood Boundaries",
        description="Official neighborhood boundaries (open data). Click one to focus it.",
        category="baseline",
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


def _line(coords: list[list[float]], **props: object) -> Feature:
    return Feature(geometry={"type": "LineString", "coordinates": coords}, properties=dict(props))


# TransLink's official route colours (from its GTFS feed's route_color column).
_TRANSLINK = {
    "expo": "#0033A0",
    "millennium": "#FFCD00",
    "canada": "#007C9F",
    "seabus": "#746661",
    "wce": "#87189D",
    "rapidbus": "#008522",
}


def _sample_skytrain_lines() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _line(
                [[-123.1119, 49.2856], [-123.0121, 49.2258], [-122.8491, 49.2258]],
                route="Expo Line (sample)",
                mode="SkyTrain",
                color=_TRANSLINK["expo"],
            ),
            _line(
                [[-123.0779, 49.2632], [-122.9411, 49.2610], [-122.7947, 49.2758]],
                route="Millennium Line (sample)",
                mode="SkyTrain",
                color=_TRANSLINK["millennium"],
            ),
            _line(
                [[-123.1119, 49.2856], [-123.1163, 49.2094], [-123.1365, 49.1666]],
                route="Canada Line (sample)",
                mode="SkyTrain",
                color=_TRANSLINK["canada"],
            ),
        ]
    )


def _sample_skytrain_stations() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(
                -123.1119,
                49.2856,
                station="Waterfront Station (sample)",
                lines="Canada Line, Expo Line",
                color="#333333",
            ),
            _point(
                -123.0121,
                49.2258,
                station="Metrotown Station (sample)",
                lines="Expo Line",
                color=_TRANSLINK["expo"],
            ),
        ]
    )


def _sample_bus_routes() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _line(
                [[-123.1140, 49.2634], [-123.0568, 49.2626], [-122.9990, 49.2610]],
                route="99 (sample)",
                name="Broadway B-Line",
                mode="Bus",
                color="#D04110",
            ),
            _line(
                [[-122.8491, 49.1913], [-122.8449, 49.1044]],
                route="R1 (sample)",
                name="King George Blvd",
                mode="Bus",
                color=_TRANSLINK["rapidbus"],
            ),
        ]
    )


def _sample_bus_stops() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-123.1140, 49.2634, stop="W Broadway @ Cambie St (sample)", routes="9, 99"),
            _point(-122.8491, 49.1913, stop="King George Stn Bay 1 (sample)", routes="R1, 321"),
        ]
    )


def _sample_seabus_wce() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _line(
                [[-123.1113, 49.2866], [-123.0829, 49.3095]],
                route="SeaBus (sample)",
                mode="Ferry",
                color=_TRANSLINK["seabus"],
            ),
            _line(
                [[-123.1119, 49.2856], [-122.8465, 49.2830], [-122.6055, 49.2172]],
                route="West Coast Express (sample)",
                mode="Commuter Rail",
                color=_TRANSLINK["wce"],
            ),
            _point(
                -123.0829,
                49.3095,
                station="Lonsdale Quay (sample)",
                lines="SeaBus",
                color=_TRANSLINK["seabus"],
            ),
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


# TTC and GO official route colours (from their GTFS feeds' route_color).
_TTC = {
    "line1": "#D5C82B",
    "line2": "#008000",
    "line4": "#B300B3",
    "streetcar": "#ED1C24",
}
_GO_LAKESHORE_WEST = "#98002E"


def _sample_gta_subway_lines() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _line(
                [[-79.4163, 43.6822], [-79.3806, 43.6459], [-79.3941, 43.7615]],
                route="Line 1 (Yonge-University) (sample)",
                mode="Subway",
                color=_TTC["line1"],
            ),
            _line(
                [[-79.5372, 43.6363], [-79.4530, 43.6559], [-79.2930, 43.6866]],
                route="Line 2 (Bloor - Danforth) (sample)",
                mode="Subway",
                color=_TTC["line2"],
            ),
            _line(
                [[-79.4113, 43.7615], [-79.3460, 43.7756]],
                route="Line 4 (Sheppard) (sample)",
                mode="Subway",
                color=_TTC["line4"],
            ),
        ]
    )


def _sample_gta_subway_stations() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(
                -79.3806,
                43.6459,
                station="Union Station (sample)",
                lines="Line 1 (Yonge-University)",
                color=_TTC["line1"],
            ),
            _point(
                -79.3995,
                43.6682,
                station="St George Station (sample)",
                lines="Line 1 (Yonge-University), Line 2 (Bloor - Danforth)",
                color="#333333",
            ),
        ]
    )


def _sample_gta_streetcar_lines() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _line(
                [[-79.4677, 43.6362], [-79.3841, 43.6497], [-79.2989, 43.6684]],
                route="501 (sample)",
                name="Queen",
                mode="Streetcar",
                color=_TTC["streetcar"],
            ),
        ]
    )


def _sample_gta_bus_routes() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _line(
                [[-79.4257, 43.7970], [-79.4113, 43.7615], [-79.3941, 43.7276]],
                route="97 (sample)",
                name="Yonge",
                mode="Bus",
                color=_TTC["streetcar"],
            ),
        ]
    )


def _sample_gta_bus_stops() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _point(-79.3841, 43.6497, stop="Queen St West @ Yonge St (sample)", routes="501"),
            _point(-79.4113, 43.7615, stop="Yonge St @ Sheppard Ave (sample)", routes="97"),
        ]
    )


def _sample_gta_go_transit() -> FeatureCollection:
    return FeatureCollection(
        features=[
            _line(
                [[-79.3806, 43.6453], [-79.5851, 43.5860], [-79.6876, 43.5155]],
                route="Lakeshore West (sample)",
                mode="GO Rail",
                color=_GO_LAKESHORE_WEST,
            ),
            _point(
                -79.3806,
                43.6453,
                station="Union Station GO (sample)",
                lines="Lakeshore West",
                color=_GO_LAKESHORE_WEST,
            ),
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


def _municipality_boundaries() -> FeatureCollection:
    return FeatureCollection(features=boundaries_service.list_boundaries("municipality"))


def _neighborhood_boundaries() -> FeatureCollection:
    return FeatureCollection(features=boundaries_service.list_boundaries("neighborhood"))


_BUILDERS: dict[str, Callable[[], FeatureCollection]] = {
    "housing-prices": _sample_housing_prices,
    "demographics": _sample_demographics,
    "skytrain-lines": _sample_skytrain_lines,
    "skytrain-stations": _sample_skytrain_stations,
    "bus-routes": _sample_bus_routes,
    "bus-stops": _sample_bus_stops,
    "seabus-wce": _sample_seabus_wce,
    "skytrain-expansion": _sample_skytrain_expansion,
    "road-construction": _sample_road_construction,
    "new-highrises": _sample_new_highrises,
    "gta-housing-prices": _sample_gta_housing_prices,
    "gta-demographics": _sample_gta_demographics,
    "gta-subway-lines": _sample_gta_subway_lines,
    "gta-subway-stations": _sample_gta_subway_stations,
    "gta-streetcar-lines": _sample_gta_streetcar_lines,
    "gta-bus-routes": _sample_gta_bus_routes,
    "gta-bus-stops": _sample_gta_bus_stops,
    "gta-go-transit": _sample_gta_go_transit,
    "gta-transit-expansion": _sample_gta_transit_expansion,
    "gta-road-construction": _sample_gta_road_construction,
    "gta-new-highrises": _sample_gta_new_highrises,
    "municipality-boundaries": _municipality_boundaries,
    "neighborhood-boundaries": _neighborhood_boundaries,
}


def _snapshot_path(layer: LayerMeta) -> Path:
    return Path(settings.data_dir) / layer.region / f"{layer.id}.geojson"


def _load_snapshot(layer: LayerMeta) -> FeatureCollection | None:
    """Load a layer's ingested GeoJSON snapshot, or None if absent/invalid."""
    path = _snapshot_path(layer)
    try:
        raw = path.read_bytes()
    except OSError:
        return None  # No snapshot ingested yet: caller falls back to samples.
    try:
        return FeatureCollection.model_validate_json(raw)
    except ValidationError:
        logger.warning("Ignoring invalid snapshot %s; serving sample data.", path)
        return None


def get_features(layer_id: str) -> FeatureCollection | None:
    """Return the FeatureCollection for a layer, or None if unknown.

    Ingested snapshots (see ``app.ingest``) win over the sample builders.
    """
    layer = get_layer(layer_id)
    if layer and (snapshot := _load_snapshot(layer)):
        return snapshot
    builder = _BUILDERS.get(layer_id)
    return builder() if builder else None
