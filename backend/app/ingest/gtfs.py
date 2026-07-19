"""Generic GTFS helpers shared by the transit ingestion modules.

``app.ingest.translink`` (GVA) and ``app.ingest.gta`` (TTC + GO Transit)
assemble their layers from these building blocks. Everything here is
agency-agnostic: callers pass the route ids to draw, a ``mode_for``/
``label_for`` naming policy, and a fallback colour for routes without a
``route_color``. All ``build_*``/``simplify_*``/``select_*`` functions are
pure and unit-tested in ``backend/tests/unit/test_ingest_gtfs.py``.
"""

from __future__ import annotations

import csv
import io
import math
import zipfile
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from app.ingest.fetch import get_bytes
from app.schemas.layers import Feature

# GTFS route_type values.
TRAM = "0"
SUBWAY = "1"
RAIL = "2"
BUS = "3"
FERRY = "4"

# Ring colour for stations served by more than one line.
INTERCHANGE_COLOR = "#333333"

# Douglas-Peucker tolerance in degrees (~9 m): keeps the committed route
# snapshots compact without visibly changing the geometry at city zooms.
SIMPLIFY_TOLERANCE_DEG = 0.00008

Rows = list[dict[str, str]]
RouteNamer = Callable[[dict[str, str]], str]


# --- pure transforms ---------------------------------------------------------


def route_color(route: dict[str, str], default: str) -> str:
    """The agency's official colour for a route, or the given fallback."""
    color = (route.get("route_color") or "").strip()
    return f"#{color.upper()}" if color else default


def route_label(route: dict[str, str]) -> str:
    """Rider-facing route name: '099' -> '99', unnumbered routes use the long name."""
    short = (route.get("route_short_name") or "").strip()
    short = short.lstrip("0") or short
    return short or (route.get("route_long_name") or "").strip()


def route_sort_key(label: str) -> tuple[int, str]:
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
    route_ids: set[str],
    mode_for: RouteNamer,
    default_color: str,
    source: str,
    label_for: RouteNamer = route_label,
    all_variants: bool = False,
) -> list[Feature]:
    """Route shapes -> LineString features carrying the agency's colours."""
    wanted = {r["route_id"]: r for r in routes if r["route_id"] in route_ids}
    shape_routes = select_shapes(trips, set(wanted), all_variants=all_variants)
    features: list[Feature] = []
    for shape_id, route_id in sorted(shape_routes.items()):
        coords = shape_coords.get(shape_id)
        if not coords or len(coords) < 2:
            continue
        route = wanted[route_id]
        label = label_for(route)
        long_name = (route.get("route_long_name") or "").strip()
        properties: dict[str, object] = {"route": label}
        if long_name and long_name != label:
            properties["name"] = long_name
        properties.update(
            {
                "mode": mode_for(route),
                "color": route_color(route, default_color),
                "source": source,
            }
        )
        features.append(
            Feature(
                geometry={"type": "LineString", "coordinates": simplify_line(coords)},
                properties=properties,
            )
        )
    return features


def station_feature(
    name: str,
    coordinates: list[float],
    line_routes: Rows,
    *,
    default_color: str,
    source: str,
    label_for: RouteNamer = route_label,
) -> Feature:
    """A station Point listing its lines, coloured like the agency's map:
    the line's colour, or a neutral ring where several lines interchange."""
    ordered = sorted(line_routes, key=label_for)
    colors = {route_color(r, default_color) for r in ordered}
    return Feature(
        geometry={"type": "Point", "coordinates": coordinates},
        properties={
            "station": name,
            "lines": ", ".join(label_for(r) for r in ordered) or None,
            "color": colors.pop() if len(colors) == 1 else INTERCHANGE_COLOR,
            "source": source,
        },
    )


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


def build_stations_from_stops(
    stops: Rows,
    stop_routes: dict[str, set[str]],
    routes: Rows,
    *,
    line_ids: set[str],
    default_color: str,
    source: str,
    clean_name: Callable[[str], str] = str.strip,
    label_for: RouteNamer = route_label,
) -> list[Feature]:
    """Derive stations for feeds without parent stations (TTC, GO).

    Street-level stops serving the given lines are grouped by their cleaned
    name (e.g. "Bay Station - Eastbound Platform" -> "Bay Station"); the
    station sits at the centroid of its platforms.
    """
    routes_by_id = {r["route_id"]: r for r in routes}
    grouped: dict[str, tuple[list[float], list[float], set[str]]] = {}
    for stop in stops:
        if (stop.get("location_type") or "0") != "0":
            continue
        served = stop_routes.get(stop["stop_id"], set()) & line_ids
        if not served:
            continue
        try:
            lng, lat = float(stop["stop_lon"]), float(stop["stop_lat"])
        except (KeyError, TypeError, ValueError):
            continue
        lngs, lats, route_ids = grouped.setdefault(clean_name(stop["stop_name"]), ([], [], set()))
        lngs.append(lng)
        lats.append(lat)
        route_ids |= served
    features: list[Feature] = []
    for name, (lngs, lats, route_ids) in sorted(grouped.items()):
        line_routes = [routes_by_id[rid] for rid in route_ids if rid in routes_by_id]
        centroid = [sum(lngs) / len(lngs), sum(lats) / len(lats)]
        features.append(
            station_feature(
                name,
                centroid,
                line_routes,
                default_color=default_color,
                source=source,
                label_for=label_for,
            )
        )
    return features


def build_bus_stops(
    stops: Rows,
    stop_routes: dict[str, set[str]],
    routes: Rows,
    *,
    surface_ids: set[str],
    source: str,
) -> list[Feature]:
    """Street-level GTFS stops -> Points listing the surface routes serving each.

    Stops that only serve non-surface routes (rail platforms in feeds without
    parent stations) are excluded - they already render as stations.
    """
    routes_by_id = {r["route_id"]: r for r in routes}
    features: list[Feature] = []
    for stop in stops:
        if (stop.get("location_type") or "0") != "0":
            continue
        if (stop.get("parent_station") or "").strip():
            continue  # station platforms already render as stations
        served = stop_routes.get(stop["stop_id"], set())
        surface = served & surface_ids
        if served and not surface:
            continue
        try:
            coordinates = [float(stop["stop_lon"]), float(stop["stop_lat"])]
        except (KeyError, TypeError, ValueError):
            continue
        labels = sorted(
            {route_label(routes_by_id[rid]) for rid in surface if rid in routes_by_id},
            key=route_sort_key,
        )
        features.append(
            Feature(
                geometry={"type": "Point", "coordinates": coordinates},
                properties={
                    "stop": stop["stop_name"],
                    "code": stop.get("stop_code") or None,
                    "routes": ", ".join(labels) or None,
                    "source": source,
                },
            )
        )
    return features


# --- feed download and parsing -----------------------------------------------


@dataclass
class GtfsFeed:
    """A parsed GTFS feed, ready for the build_* functions."""

    routes: Rows
    trips: Rows
    stops: Rows
    shape_coords: dict[str, list[list[float]]]
    stop_routes: dict[str, set[str]]

    def route_ids(self, *route_types: str) -> set[str]:
        return {r["route_id"] for r in self.routes if r.get("route_type") in route_types}


def read_csv(archive: zipfile.ZipFile, name: str) -> Rows:
    with archive.open(name) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")))


def shape_index(shape_rows: Rows) -> dict[str, list[list[float]]]:
    grouped: defaultdict[str, list[tuple[int, list[float]]]] = defaultdict(list)
    for row in shape_rows:
        point = [float(row["shape_pt_lon"]), float(row["shape_pt_lat"])]
        grouped[row["shape_id"]].append((int(row["shape_pt_sequence"]), point))
    return {
        shape_id: [point for _, point in sorted(points, key=lambda item: item[0])]
        for shape_id, points in grouped.items()
    }


def scan_stop_routes(archive: zipfile.ZipFile, trip_routes: dict[str, str]) -> dict[str, set[str]]:
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


def load_feed(url: str) -> GtfsFeed:
    """Download a GTFS zip and parse the tables the layer builders need."""
    archive = zipfile.ZipFile(io.BytesIO(get_bytes(url)))
    routes = read_csv(archive, "routes.txt")
    trips = read_csv(archive, "trips.txt")
    stops = read_csv(archive, "stops.txt")
    shape_coords = shape_index(read_csv(archive, "shapes.txt"))
    stop_routes = scan_stop_routes(archive, {t["trip_id"]: t["route_id"] for t in trips})
    return GtfsFeed(routes, trips, stops, shape_coords, stop_routes)
