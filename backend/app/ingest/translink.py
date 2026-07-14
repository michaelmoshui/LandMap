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

Fetching and transforming are kept separate: the ``build_*``/``simplify_*``
functions are pure and unit-tested in ``backend/tests/unit/test_ingest_translink.py``.
"""

from __future__ import annotations

import csv
import functools
import io
import math
import zipfile
from collections import Counter, defaultdict

from app.ingest.fetch import get_bytes
from app.schemas.layers import Feature, FeatureCollection

GTFS_URL = "https://gtfs-static.translink.ca/gtfs/google_transit.zip"
SOURCE = "TransLink GTFS static feed"

# GTFS route_type values used by TransLink.
SKYTRAIN = "1"  # subway/metro
COMMUTER_RAIL = "2"  # West Coast Express
BUS = "3"
FERRY = "4"  # SeaBus
RAIL_AND_FERRY = {SKYTRAIN, COMMUTER_RAIL, FERRY}

_MODE_BY_TYPE = {SKYTRAIN: "SkyTrain", COMMUTER_RAIL: "Commuter Rail", BUS: "Bus", FERRY: "Ferry"}

# Local routes carry no route_color in the feed; TransLink's system map draws
# them in a gray-blue.
DEFAULT_BUS_COLOR = "#7A99AC"
# Ring colour for stations served by more than one line.
INTERCHANGE_COLOR = "#333333"

# Douglas-Peucker tolerance in degrees (~9 m): keeps the committed bus-route
# snapshot compact without visibly changing the geometry at city zooms.
SIMPLIFY_TOLERANCE_DEG = 0.00008

Rows = list[dict[str, str]]


# --- pure transforms ---------------------------------------------------------


def route_color(route: dict[str, str]) -> str:
    """TransLink's official colour for a route, or the local-bus fallback."""
    color = (route.get("route_color") or "").strip()
    return f"#{color.upper()}" if color else DEFAULT_BUS_COLOR


def route_label(route: dict[str, str]) -> str:
    """Rider-facing route name: '099' -> '99', rail routes use the long name."""
    short = (route.get("route_short_name") or "").strip()
    short = short.lstrip("0") or short
    return short or (route.get("route_long_name") or "").strip()


def _route_sort_key(label: str) -> tuple[int, str]:
    digits = "".join(ch for ch in label if ch.isdigit())
    return (int(digits) if digits else 0, label)


def simplify_line(
    coords: list[list[float]], tolerance: float = SIMPLIFY_TOLERANCE_DEG
) -> list[list[float]]:
    """Douglas-Peucker on [lng, lat] pairs (planar, lng scaled by cos(lat))."""
    deduped = [coords[0]] + [b for a, b in zip(coords, coords[1:], strict=False) if b != a]
    if len(deduped) <= 2:
        return deduped
    kx = math.cos(math.radians(deduped[0][1]))  # metres per degree ratio lng/lat
    keep = [False] * len(deduped)
    keep[0] = keep[-1] = True
    stack = [(0, len(deduped) - 1)]
    while stack:
        first, last = stack.pop()
        ax, ay = deduped[first][0] * kx, deduped[first][1]
        bx, by = deduped[last][0] * kx, deduped[last][1]
        dx, dy = bx - ax, by - ay
        seg2 = dx * dx + dy * dy
        worst, worst_d2 = -1, tolerance * tolerance
        for i in range(first + 1, last):
            px, py = deduped[i][0] * kx - ax, deduped[i][1] - ay
            t = max(0.0, min(1.0, (px * dx + py * dy) / seg2)) if seg2 else 0.0
            d2 = (px - t * dx) ** 2 + (py - t * dy) ** 2
            if d2 > worst_d2:
                worst, worst_d2 = i, d2
        if worst != -1:
            keep[worst] = True
            stack += [(first, worst), (worst, last)]
    return [point for point, kept in zip(deduped, keep, strict=True) if kept]


def select_shapes(trips: Rows, route_ids: set[str], *, all_variants: bool) -> dict[str, str]:
    """Map shape_id -> route_id for the shapes worth drawing.

    ``all_variants`` keeps every distinct shape (rail branches must all
    render); otherwise only the busiest shape per direction survives, which
    is how transit maps usually draw bus routes (short-turn and detour
    variants collapse into the main alignment).
    """
    if all_variants:
        return {
            trip["shape_id"]: trip["route_id"]
            for trip in trips
            if trip["route_id"] in route_ids and trip.get("shape_id")
        }
    counts: Counter[tuple[str, str, str]] = Counter()
    for trip in trips:
        if trip["route_id"] in route_ids and trip.get("shape_id"):
            counts[(trip["route_id"], trip.get("direction_id", ""), trip["shape_id"])] += 1
    best: dict[tuple[str, str], tuple[int, str]] = {}
    for (route_id, direction, shape_id), n in counts.items():
        if (n, shape_id) > best.get((route_id, direction), (0, "")):
            best[(route_id, direction)] = (n, shape_id)
    return {shape_id: route_id for (route_id, _), (_, shape_id) in best.items()}


def build_route_lines(
    routes: Rows,
    trips: Rows,
    shape_coords: dict[str, list[list[float]]],
    *,
    route_types: set[str],
    all_variants: bool = False,
) -> list[Feature]:
    """Route shapes -> LineString features carrying TransLink colours."""
    wanted = {r["route_id"]: r for r in routes if r.get("route_type") in route_types}
    shape_routes = select_shapes(trips, set(wanted), all_variants=all_variants)
    features: list[Feature] = []
    for shape_id, route_id in sorted(shape_routes.items()):
        coords = shape_coords.get(shape_id)
        if not coords or len(coords) < 2:
            continue
        route = wanted[route_id]
        label = route_label(route)
        long_name = (route.get("route_long_name") or "").strip()
        properties: dict[str, object] = {"route": label}
        if long_name and long_name != label:
            properties["name"] = long_name
        properties.update(
            {
                "mode": _MODE_BY_TYPE.get(route["route_type"], "Transit"),
                "color": route_color(route),
                "source": SOURCE,
            }
        )
        features.append(
            Feature(
                geometry={"type": "LineString", "coordinates": simplify_line(coords)},
                properties=properties,
            )
        )
    return features


def station_route_index(stops: Rows, stop_routes: dict[str, set[str]]) -> dict[str, set[str]]:
    """Map station stop_id -> route_ids calling there (via child platforms)."""
    index: defaultdict[str, set[str]] = defaultdict(set)
    for stop in stops:
        served = stop_routes.get(stop["stop_id"], set())
        if stop.get("location_type") == "1":
            index[stop["stop_id"]] |= served
        elif parent := (stop.get("parent_station") or "").strip():
            index[parent] |= served
    return dict(index)


def build_stations(
    stops: Rows, stop_routes: dict[str, set[str]], routes: Rows
) -> tuple[list[Feature], list[Feature]]:
    """GTFS parent stations -> (SkyTrain stations, SeaBus/WCE stations).

    Stations get the colour of their line, or a neutral ring when several
    lines interchange - the look of TransLink's system map.
    """
    routes_by_id = {r["route_id"]: r for r in routes}
    index = station_route_index(stops, stop_routes)
    skytrain: list[Feature] = []
    other: list[Feature] = []
    for stop in stops:
        if stop.get("location_type") != "1":
            continue
        rail_routes = sorted(
            (
                routes_by_id[rid]
                for rid in index.get(stop["stop_id"], set())
                if routes_by_id.get(rid, {}).get("route_type") in RAIL_AND_FERRY
            ),
            key=route_label,
        )
        colors = {route_color(r) for r in rail_routes}
        feature = Feature(
            geometry={
                "type": "Point",
                "coordinates": [float(stop["stop_lon"]), float(stop["stop_lat"])],
            },
            properties={
                "station": stop["stop_name"],
                "lines": ", ".join(route_label(r) for r in rail_routes) or None,
                "color": colors.pop() if len(colors) == 1 else INTERCHANGE_COLOR,
                "source": SOURCE,
            },
        )
        # Stations with no detected rail service default to the SkyTrain layer.
        if any(r["route_type"] == SKYTRAIN for r in rail_routes) or not rail_routes:
            skytrain.append(feature)
        else:
            other.append(feature)
    return skytrain, other


def build_bus_stops(stops: Rows, stop_routes: dict[str, set[str]], routes: Rows) -> list[Feature]:
    """Street-level GTFS stops -> Points listing the bus routes serving each."""
    routes_by_id = {r["route_id"]: r for r in routes}
    features: list[Feature] = []
    for stop in stops:
        if (stop.get("location_type") or "0") != "0":
            continue
        if (stop.get("parent_station") or "").strip():
            continue  # station platforms already render as stations
        try:
            coordinates = [float(stop["stop_lon"]), float(stop["stop_lat"])]
        except (KeyError, TypeError, ValueError):
            continue
        labels = sorted(
            {
                route_label(routes_by_id[rid])
                for rid in stop_routes.get(stop["stop_id"], set())
                if routes_by_id.get(rid, {}).get("route_type") == BUS
            },
            key=_route_sort_key,
        )
        features.append(
            Feature(
                geometry={"type": "Point", "coordinates": coordinates},
                properties={
                    "stop": stop["stop_name"],
                    "code": stop.get("stop_code") or None,
                    "routes": ", ".join(labels) or None,
                    "source": SOURCE,
                },
            )
        )
    return features


# --- feed download and assembly ----------------------------------------------


def _read_csv(archive: zipfile.ZipFile, name: str) -> Rows:
    with archive.open(name) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")))


def _shape_index(shape_rows: Rows) -> dict[str, list[list[float]]]:
    grouped: defaultdict[str, list[tuple[int, list[float]]]] = defaultdict(list)
    for row in shape_rows:
        point = [float(row["shape_pt_lon"]), float(row["shape_pt_lat"])]
        grouped[row["shape_id"]].append((int(row["shape_pt_sequence"]), point))
    return {
        shape_id: [point for _, point in sorted(points, key=lambda item: item[0])]
        for shape_id, points in grouped.items()
    }


def _scan_stop_routes(archive: zipfile.ZipFile, trip_routes: dict[str, str]) -> dict[str, set[str]]:
    """Stream stop_times.txt (too big to load) into stop_id -> route_ids."""
    stop_routes: defaultdict[str, set[str]] = defaultdict(set)
    with archive.open("stop_times.txt") as fh:
        reader = csv.reader(io.TextIOWrapper(fh, encoding="utf-8-sig", newline=""))
        header = next(reader)
        trip_col, stop_col = header.index("trip_id"), header.index("stop_id")
        for row in reader:
            if route_id := trip_routes.get(row[trip_col]):
                stop_routes[row[stop_col]].add(route_id)
    return dict(stop_routes)


@functools.lru_cache(maxsize=1)
def _layer_collections() -> dict[str, FeatureCollection]:
    """Download the GTFS feed once and build every transit layer from it."""
    archive = zipfile.ZipFile(io.BytesIO(get_bytes(GTFS_URL)))
    routes = _read_csv(archive, "routes.txt")
    trips = _read_csv(archive, "trips.txt")
    stops = _read_csv(archive, "stops.txt")
    shape_coords = _shape_index(_read_csv(archive, "shapes.txt"))
    stop_routes = _scan_stop_routes(archive, {t["trip_id"]: t["route_id"] for t in trips})

    skytrain_stations, seabus_wce_stations = build_stations(stops, stop_routes, routes)
    return {
        "skytrain-lines": FeatureCollection(
            features=build_route_lines(
                routes, trips, shape_coords, route_types={SKYTRAIN}, all_variants=True
            )
        ),
        "skytrain-stations": FeatureCollection(features=skytrain_stations),
        "bus-routes": FeatureCollection(
            features=build_route_lines(routes, trips, shape_coords, route_types={BUS})
        ),
        "bus-stops": FeatureCollection(features=build_bus_stops(stops, stop_routes, routes)),
        "seabus-wce": FeatureCollection(
            features=build_route_lines(
                routes, trips, shape_coords, route_types={COMMUTER_RAIL, FERRY}, all_variants=True
            )
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
