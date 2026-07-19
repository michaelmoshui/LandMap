"""TransLink GTFS ingestion: the GVA transit network layers.

One download of TransLink's GTFS static feed (see SOURCES.md) feeds five
layers:

- ``skytrain-lines``     SkyTrain alignments (Expo, Millennium, Canada Line),
  every shape variant so branches render.
- ``skytrain-stations``  Stations served by SkyTrain, with the lines calling
  at each and the official line colour (interchanges get a neutral ring).
- ``bus-routes``         Every bus route, drawn as its busiest shape per
  direction so the snapshot stays compact.
- ``bus-stops``          Every bus stop with the routes serving it.
- ``seabus-wce``         SeaBus and West Coast Express routes plus their
  stations/terminals.

The feed's ``route_color`` column carries TransLink's official colours
(Expo #0033A0, Millennium #FFCD00, Canada Line #007C9F, RapidBus #008522,
99 B-Line #D04110, SeaBus #746661, WCE #87189D); each feature gets a
``color`` property the frontend renders directly. Regular buses have no
colour in the feed and fall back to the gray-blue TransLink draws local
routes with on its system map.

The generic GTFS transforms live in ``app.ingest.gtfs``; this module only
holds the TransLink feed URL and its naming/partitioning policy.
"""

from __future__ import annotations

import functools

from app.ingest import gtfs
from app.schemas.layers import Feature, FeatureCollection

GTFS_URL = "https://gtfs-static.translink.ca/gtfs/google_transit.zip"
SOURCE = "TransLink GTFS static feed"

RAIL_AND_FERRY = {gtfs.SUBWAY, gtfs.RAIL, gtfs.FERRY}

_MODE_BY_TYPE = {
    gtfs.SUBWAY: "SkyTrain",
    gtfs.RAIL: "Commuter Rail",
    gtfs.BUS: "Bus",
    gtfs.FERRY: "Ferry",
}

# Local routes carry no route_color in the feed; TransLink's system map draws
# them in a gray-blue.
DEFAULT_BUS_COLOR = "#7A99AC"


def _mode_for(route: dict[str, str]) -> str:
    return _MODE_BY_TYPE.get(route.get("route_type", ""), "Transit")


def build_stations(
    stops: gtfs.Rows, stop_routes: dict[str, set[str]], routes: gtfs.Rows
) -> tuple[list[Feature], list[Feature]]:
    """GTFS parent stations -> (SkyTrain stations, SeaBus/WCE stations)."""
    routes_by_id = {r["route_id"]: r for r in routes}
    index = gtfs.station_route_index(stops, stop_routes)
    skytrain: list[Feature] = []
    other: list[Feature] = []
    for stop in stops:
        if stop.get("location_type") != "1":
            continue
        rail_routes = [
            routes_by_id[rid]
            for rid in index.get(stop["stop_id"], set())
            if routes_by_id.get(rid, {}).get("route_type") in RAIL_AND_FERRY
        ]
        feature = gtfs.station_feature(
            stop["stop_name"],
            [float(stop["stop_lon"]), float(stop["stop_lat"])],
            rail_routes,
            default_color=DEFAULT_BUS_COLOR,
            source=SOURCE,
        )
        # Stations with no detected rail service default to the SkyTrain layer.
        if any(r["route_type"] == gtfs.SUBWAY for r in rail_routes) or not rail_routes:
            skytrain.append(feature)
        else:
            other.append(feature)
    return skytrain, other


@functools.lru_cache(maxsize=1)
def _layer_collections() -> dict[str, FeatureCollection]:
    """Download the GTFS feed once and build every transit layer from it."""
    feed = gtfs.load_feed(GTFS_URL)
    lines = functools.partial(
        gtfs.build_route_lines,
        feed.routes,
        feed.trips,
        feed.shape_coords,
        mode_for=_mode_for,
        default_color=DEFAULT_BUS_COLOR,
        source=SOURCE,
    )
    skytrain_stations, seabus_wce_stations = build_stations(
        feed.stops, feed.stop_routes, feed.routes
    )
    return {
        "skytrain-lines": FeatureCollection(
            features=lines(route_ids=feed.route_ids(gtfs.SUBWAY), all_variants=True)
        ),
        "skytrain-stations": FeatureCollection(features=skytrain_stations),
        "bus-routes": FeatureCollection(features=lines(route_ids=feed.route_ids(gtfs.BUS))),
        "bus-stops": FeatureCollection(
            features=gtfs.build_bus_stops(
                feed.stops,
                feed.stop_routes,
                feed.routes,
                surface_ids=feed.route_ids(gtfs.BUS),
                source=SOURCE,
            )
        ),
        "seabus-wce": FeatureCollection(
            features=lines(route_ids=feed.route_ids(gtfs.RAIL, gtfs.FERRY), all_variants=True)
            + seabus_wce_stations
        ),
    }


def fetch_skytrain_lines() -> FeatureCollection:
    return _layer_collections()["skytrain-lines"]


def fetch_skytrain_stations() -> FeatureCollection:
    return _layer_collections()["skytrain-stations"]


def fetch_bus_routes() -> FeatureCollection:
    return _layer_collections()["bus-routes"]


def fetch_bus_stops() -> FeatureCollection:
    return _layer_collections()["bus-stops"]


def fetch_seabus_wce() -> FeatureCollection:
    return _layer_collections()["seabus-wce"]
