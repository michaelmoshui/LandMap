"""Greater Toronto Area transit ingestion: TTC and GO Transit GTFS feeds.

Two downloads feed six layers (sources in SOURCES.md):

- ``gta-subway-lines``     TTC rapid transit Lines 1-6 (subway + the Line 5/6
  LRTs), busiest shape per direction (TTC lines have no branches, and the
  busiest pattern is the full line; short turns would only add overdraw).
- ``gta-subway-stations``  Stations derived by grouping the feed's platform
  stops ("Bay Station - Eastbound Platform" -> "Bay Station"), with the lines
  calling at each and the official line colour.
- ``gta-streetcar-lines``  The streetcar network (501-512 day routes in TTC
  red, 300-series night routes in blue), busiest shape per direction.
- ``gta-bus-routes``       Every TTC bus route, busiest shape per direction.
- ``gta-bus-stops``        Every TTC bus and streetcar stop with the routes
  serving it.
- ``gta-go-transit``       GO train lines and their stations in Metrolinx's
  official line colours.

Both feeds colour every route (TTC: Line 1 #D5C82B, Line 2 #008000, Line 4
#B300B3, streetcars #ED1C24, night routes #0054A6, express #00A651; GO: one
colour per corridor), so features carry the agencies' real palettes. Neither
feed declares parent stations, so stations are derived from the stops served
by rail routes (see ``gtfs.build_stations_from_stops``).

Run inside the backend container (or a host venv) to refresh the snapshots:

    python -m app.ingest.gta [layer-id ...]

The generic GTFS transforms live in ``app.ingest.gtfs``; the TTC-specific
policies below are unit-tested in ``backend/tests/unit/test_ingest_gta.py``.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import sys
from pathlib import Path

from app.core.config import settings
from app.ingest import gtfs
from app.schemas.layers import FeatureCollection

TTC_GTFS_URL = (
    "http://opendata.toronto.ca/toronto.transit.commission/"
    "ttc-routes-and-schedules/OpenData_TTC_Schedules.zip"
)
GO_GTFS_URL = "https://assets.metrolinx.com/raw/upload/Documents/Metrolinx/Open%20Data/GO-GTFS.zip"

TTC_SOURCE = "TTC GTFS static feed"
GO_SOURCE = "GO Transit (Metrolinx) GTFS static feed"

# Both feeds colour every route today; these only guard against future gaps.
TTC_DEFAULT_COLOR = "#ED1C24"  # TTC red
GO_DEFAULT_COLOR = "#00583C"  # GO brand green

# Strip the feed's platform suffixes down to the station itself:
# "Bay Station - Eastbound Platform", "Mount Dennis Station LRT Platform",
# "Kennedy Station - Subway Platform", and "Union Station - Northbound
# Platform Towards Finch" all collapse to their station.
_PLATFORM_RE = re.compile(
    r"\s*-?\s*(?:(?:north|south|east|west)bound|subway|lrt)\s+platform(?:\s+towards\s+.*)?$",
    re.IGNORECASE,
)


def clean_station_name(name: str) -> str:
    return _PLATFORM_RE.sub("", name).strip(" -")


def rapid_transit_ids(routes: gtfs.Rows) -> set[str]:
    """TTC rapid transit: the subway plus the single-digit LRT Lines (5, 6),
    which the feed types as trams alongside the 3-digit streetcars."""
    ids = set()
    for route in routes:
        short = (route.get("route_short_name") or "").strip()
        if route.get("route_type") == gtfs.SUBWAY or (
            route.get("route_type") == gtfs.TRAM and len(short) == 1
        ):
            ids.add(route["route_id"])
    return ids


def streetcar_ids(routes: gtfs.Rows) -> set[str]:
    return {r["route_id"] for r in routes if r.get("route_type") == gtfs.TRAM} - rapid_transit_ids(
        routes
    )


def ttc_mode(route: dict[str, str]) -> str:
    if route.get("route_type") == gtfs.SUBWAY:
        return "Subway"
    if route.get("route_type") == gtfs.TRAM:
        return "LRT" if len((route.get("route_short_name") or "").strip()) == 1 else "Streetcar"
    return "Bus"


def line_label(route: dict[str, str]) -> str:
    """Rail lines read best by their long name ('Line 1 (Yonge-University)',
    'Lakeshore West') rather than the short code ('1', 'LW')."""
    return (route.get("route_long_name") or "").strip() or gtfs.route_label(route)


@functools.lru_cache(maxsize=1)
def _ttc_collections() -> dict[str, FeatureCollection]:
    """Download the TTC feed once and build its five layers from it."""
    feed = gtfs.load_feed(TTC_GTFS_URL)
    rapid = rapid_transit_ids(feed.routes)
    streetcar = streetcar_ids(feed.routes)
    bus = feed.route_ids(gtfs.BUS)
    lines = functools.partial(
        gtfs.build_route_lines,
        feed.routes,
        feed.trips,
        feed.shape_coords,
        mode_for=ttc_mode,
        default_color=TTC_DEFAULT_COLOR,
        source=TTC_SOURCE,
    )
    return {
        "gta-subway-lines": FeatureCollection(
            features=lines(route_ids=rapid, label_for=line_label)
        ),
        "gta-subway-stations": FeatureCollection(
            features=gtfs.build_stations_from_stops(
                feed.stops,
                feed.stop_routes,
                feed.routes,
                line_ids=rapid,
                clean_name=clean_station_name,
                label_for=line_label,
                default_color=TTC_DEFAULT_COLOR,
                source=TTC_SOURCE,
            )
        ),
        "gta-streetcar-lines": FeatureCollection(features=lines(route_ids=streetcar)),
        "gta-bus-routes": FeatureCollection(features=lines(route_ids=bus)),
        "gta-bus-stops": FeatureCollection(
            features=gtfs.build_bus_stops(
                feed.stops,
                feed.stop_routes,
                feed.routes,
                surface_ids=streetcar | bus,
                source=TTC_SOURCE,
            )
        ),
    }


@functools.lru_cache(maxsize=1)
def _go_collections() -> dict[str, FeatureCollection]:
    """Download the GO feed once and build the rail layer (trains + stations)."""
    feed = gtfs.load_feed(GO_GTFS_URL)
    rail = feed.route_ids(gtfs.RAIL)
    lines = gtfs.build_route_lines(
        feed.routes,
        feed.trips,
        feed.shape_coords,
        route_ids=rail,
        mode_for=lambda _route: "GO Rail",
        label_for=line_label,
        default_color=GO_DEFAULT_COLOR,
        source=GO_SOURCE,
    )
    stations = gtfs.build_stations_from_stops(
        feed.stops,
        feed.stop_routes,
        feed.routes,
        line_ids=rail,
        label_for=line_label,
        default_color=GO_DEFAULT_COLOR,
        source=GO_SOURCE,
    )
    return {"gta-go-transit": FeatureCollection(features=lines + stations)}


def fetch_gta_subway_lines() -> FeatureCollection:
    return _ttc_collections()["gta-subway-lines"]


def fetch_gta_subway_stations() -> FeatureCollection:
    return _ttc_collections()["gta-subway-stations"]


def fetch_gta_streetcar_lines() -> FeatureCollection:
    return _ttc_collections()["gta-streetcar-lines"]


def fetch_gta_bus_routes() -> FeatureCollection:
    return _ttc_collections()["gta-bus-routes"]


def fetch_gta_bus_stops() -> FeatureCollection:
    return _ttc_collections()["gta-bus-stops"]


def fetch_gta_go_transit() -> FeatureCollection:
    return _go_collections()["gta-go-transit"]


# --- CLI --------------------------------------------------------------------

BUILDERS = {
    "gta-subway-lines": fetch_gta_subway_lines,
    "gta-subway-stations": fetch_gta_subway_stations,
    "gta-streetcar-lines": fetch_gta_streetcar_lines,
    "gta-bus-routes": fetch_gta_bus_routes,
    "gta-bus-stops": fetch_gta_bus_stops,
    "gta-go-transit": fetch_gta_go_transit,
}


def snapshot_dir() -> Path:
    return Path(settings.data_dir) / "gta"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh GTA layer snapshots.")
    parser.add_argument(
        "layers",
        nargs="*",
        metavar="layer-id",
        help=f"layers to refresh (default: all of {', '.join(BUILDERS)})",
    )
    args = parser.parse_args(argv)
    if unknown := [layer for layer in args.layers if layer not in BUILDERS]:
        parser.error(f"unknown layer(s): {', '.join(unknown)}")
    targets = args.layers or list(BUILDERS)

    out_dir = snapshot_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    failed = False
    for layer_id in targets:
        try:
            collection = BUILDERS[layer_id]()
        except Exception as exc:  # noqa: BLE001 - keep refreshing the other layers
            print(f"FAIL {layer_id}: {exc}", file=sys.stderr)
            failed = True
            continue
        path = out_dir / f"{layer_id}.geojson"
        payload = collection.model_dump(exclude_none=False)
        path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
        print(f"ok   {layer_id}: {len(collection.features)} features -> {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
