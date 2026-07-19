"""Greater Vancouver Area ingestion: real data for the five GVA layers.

Sources (see SOURCES.md):

- ``housing-prices``   City of Vancouver ``property-tax-report`` (assessed
  values aggregated by BCA neighbourhood code), joined to the 22 local-area
  polygons via the ``property-addresses`` dataset.
- ``demographics``     Statistics Canada 2021 Census population and dwelling
  counts per Metro Vancouver census subdivision, served by Esri Canada's
  public FeatureServer.
- ``skytrain-expansion``  OpenStreetMap (Overpass API): under-construction
  SkyTrain alignments (Broadway Extension, Surrey-Langley) and their station
  construction sites. Data (c) OpenStreetMap contributors, ODbL.
- ``road-construction``   City of Vancouver "Road Ahead" datasets (projects
  under construction + upcoming projects).
- ``new-highrises``    City of Vancouver ``issued-building-permits``: new
  residential buildings worth $20M+ issued since 2023.
- ``skytrain-lines``, ``skytrain-stations``, ``bus-routes``, ``bus-stops``,
  ``seabus-wce``    TransLink GTFS static feed (see ``app.ingest.translink``).

Run inside the backend container (or a host venv) to refresh the snapshots:

    python -m app.ingest.gva [layer-id ...]

Fetching and transforming are kept separate: ``transform_*``/``merge_*`` are
pure functions unit-tested in ``backend/tests/unit/test_ingest_gva.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.ingest import translink
from app.ingest.fetch import get_json, post_form_json
from app.schemas.layers import Feature, FeatureCollection

COV_API = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets"

CENSUS_QUERY_URL = (
    "https://services.arcgis.com/wjcPoefzjpzCgffS/arcgis/rest/services/"
    "Canadian_Population_and_Dwelling_Counts_2021/FeatureServer/2/query"
)
METRO_VAN_CSD_PREFIX = "5915"

# Main instance plus mirrors; tried in order because the primary rate-limits.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
# Metro Vancouver bounding box: (south, west, north, east).
GVA_BBOX = "49.0,-123.3,49.35,-122.4"
# Ways west of this longitude belong to the Broadway Extension; the rest is
# the Surrey-Langley project (the two builds are ~15 km apart).
BROADWAY_MAX_LNG = -123.0

HIGHRISE_MIN_VALUE = 20_000_000
HIGHRISE_SINCE = "2023-01-01"


# --- housing-prices ---------------------------------------------------------


def fetch_housing_prices() -> FeatureCollection:
    year = _latest_tax_report_year()
    code_stats: dict[str, dict[str, dict[str, float]]] = {}
    for legal_type in ("STRATA", "LAND"):
        rows = get_json(
            f"{COV_API}/property-tax-report/records",
            {
                "select": (
                    "neighbourhood_code, count(*) as n, "
                    "avg(current_land_value + current_improvement_value) as avg_value"
                ),
                "where": f"report_year='{year}' and legal_type='{legal_type}'",
                "group_by": "neighbourhood_code",
                "limit": "100",
            },
        )["results"]
        code_stats[legal_type] = {
            row["neighbourhood_code"]: {"n": row["n"], "avg_value": row["avg_value"]}
            for row in rows
            if row.get("neighbourhood_code") and row.get("avg_value")
        }

    codes = sorted(set(code_stats["STRATA"]) | set(code_stats["LAND"]))
    code_to_area = {code: _local_area_for_code(code, year) for code in codes}
    boundaries = get_json(f"{COV_API}/local-area-boundary/exports/geojson")
    return merge_housing(boundaries, code_stats, code_to_area, year)


def _latest_tax_report_year() -> str:
    rows = get_json(
        f"{COV_API}/property-tax-report/records",
        {"select": "report_year", "group_by": "report_year", "limit": "100"},
    )["results"]
    return max(row["report_year"] for row in rows)


def _local_area_for_code(code: str, year: str) -> str | None:
    """Map a tax-report neighbourhood code to a local area by sampling parcels.

    The tax report has no geometry, but its ``land_coordinate`` joins to the
    ``property-addresses`` dataset, which carries ``geo_local_area``. A
    majority vote over a few parcels pins the code to one local area.
    """
    rows = get_json(
        f"{COV_API}/property-tax-report/records",
        {
            "select": "land_coordinate",
            "where": f"neighbourhood_code='{code}' and report_year='{year}'",
            "limit": "8",
        },
    )["results"]
    coords = sorted({row["land_coordinate"] for row in rows if row.get("land_coordinate")})
    if not coords:
        return None
    quoted = ", ".join(f"'{coord}'" for coord in coords)
    rows = get_json(
        f"{COV_API}/property-addresses/records",
        {"select": "geo_local_area", "where": f"pcoord in ({quoted})", "limit": "20"},
    )["results"]
    votes = Counter(row["geo_local_area"] for row in rows if row.get("geo_local_area"))
    return votes.most_common(1)[0][0] if votes else None


def merge_housing(
    boundaries: dict[str, Any],
    code_stats: dict[str, dict[str, dict[str, float]]],
    code_to_area: dict[str, str | None],
    year: str,
) -> FeatureCollection:
    """Combine per-code assessment averages into local-area polygon features."""
    area_stats: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for legal_type, per_code in code_stats.items():
        totals: dict[str, dict[str, float]] = defaultdict(lambda: {"n": 0.0, "sum": 0.0})
        for code, stats in per_code.items():
            area = code_to_area.get(code)
            if not area:
                continue
            totals[area]["n"] += stats["n"]
            totals[area]["sum"] += stats["avg_value"] * stats["n"]
        for area, total in totals.items():
            area_stats[area][legal_type] = {
                "n": total["n"],
                "avg_value": total["sum"] / total["n"],
            }

    features: list[Feature] = []
    for raw in boundaries.get("features", []):
        name = (raw.get("properties") or {}).get("name")
        geometry = raw.get("geometry")
        if not name or not geometry:
            continue
        stats = area_stats.get(name, {})
        strata = stats.get("STRATA")
        land = stats.get("LAND")
        features.append(
            Feature(
                geometry=geometry,
                properties={
                    "area": name,
                    "assessment_year": year,
                    "strata_avg_value": round(strata["avg_value"]) if strata else None,
                    "strata_count": int(strata["n"]) if strata else 0,
                    "land_avg_value": round(land["avg_value"]) if land else None,
                    "land_count": int(land["n"]) if land else 0,
                    "source": "City of Vancouver property tax report",
                },
            )
        )
    return FeatureCollection(features=features)


# --- demographics -----------------------------------------------------------


def fetch_demographics() -> FeatureCollection:
    raw = get_json(
        CENSUS_QUERY_URL,
        {
            "where": f"CSDUID LIKE '{METRO_VAN_CSD_PREFIX}%'",
            "outFields": (
                "CSDNAME,CSDTYPED,Population2021,Population2016,PopPctChange16to21,"
                "TotPrivDwellings2021,PopPerSqKm2021,LandAreaSqKm2021"
            ),
            "returnGeometry": "true",
            "outSR": "4326",
            "geometryPrecision": "4",
            "maxAllowableOffset": "0.0005",
            "f": "geojson",
        },
    )
    return transform_census(raw)


def transform_census(raw: dict[str, Any]) -> FeatureCollection:
    """StatCan census-subdivision GeoJSON -> demographics FeatureCollection."""
    features: list[Feature] = []
    for feature in raw.get("features", []):
        geometry = feature.get("geometry")
        props = feature.get("properties") or {}
        if not geometry or props.get("Population2021") is None:
            continue
        features.append(
            Feature(
                geometry=geometry,
                properties={
                    "municipality": props.get("CSDNAME"),
                    "type": props.get("CSDTYPED"),
                    "population_2021": props.get("Population2021"),
                    "population_2016": props.get("Population2016"),
                    "pop_change_pct": props.get("PopPctChange16to21"),
                    "dwellings": props.get("TotPrivDwellings2021"),
                    "density_per_km2": props.get("PopPerSqKm2021"),
                    "area_km2": props.get("LandAreaSqKm2021"),
                    "source": "Statistics Canada, 2021 Census",
                },
            )
        )
    return FeatureCollection(features=features)


# --- skytrain-expansion -----------------------------------------------------

_OVERPASS_QUERY = f"""
[out:json][timeout:90];
(
  way["railway"="construction"]["construction"~"subway|light_rail"]({GVA_BBOX});
  way["landuse"="construction"]["name"~"Station"]({GVA_BBOX});
);
out geom;
"""

_STATION_NOISE_RE = re.compile(
    r"^(?:Surrey Langley SkyTrain Project|SLS Project|SLS)\s*-\s*|"
    r"\s*(?:Station\s+)?Construction(?:\s+Area)?$"
)


def fetch_skytrain_expansion() -> FeatureCollection:
    last_error: Exception | None = None
    for url in OVERPASS_URLS:
        try:
            raw = post_form_json(url, {"data": _OVERPASS_QUERY})
            return transform_overpass(raw)
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(f"All Overpass endpoints failed: {last_error}")


def _project_for_lng(lng: float) -> str:
    if lng <= BROADWAY_MAX_LNG:
        return "Millennium Line Broadway Extension"
    return "Surrey-Langley SkyTrain"


def _station_name(raw_name: str) -> str:
    name = _STATION_NOISE_RE.sub("", raw_name).strip(" -")
    return name if name.endswith("Station") else f"{name} Station"


def transform_overpass(raw: dict[str, Any]) -> FeatureCollection:
    """Overpass ways -> alignment LineStrings + station construction Points."""
    features: list[Feature] = []
    for element in raw.get("elements", []):
        if element.get("type") != "way" or not element.get("geometry"):
            continue
        tags = element.get("tags", {})
        coords = [[point["lon"], point["lat"]] for point in element["geometry"]]
        mean_lng = sum(lng for lng, _ in coords) / len(coords)
        project = _project_for_lng(mean_lng)
        if tags.get("railway") == "construction":
            properties = {
                "project": project,
                "status": "under-construction",
                "source": "OpenStreetMap contributors (ODbL)",
            }
            if tags.get("name"):
                properties["segment"] = tags["name"]
            if tags.get("opening_date"):
                properties["opens"] = tags["opening_date"]
            geometry = {"type": "LineString", "coordinates": coords}
            features.append(Feature(geometry=geometry, properties=properties))
        elif "Station" in tags.get("name", ""):
            mean_lat = sum(lat for _, lat in coords) / len(coords)
            features.append(
                Feature(
                    geometry={"type": "Point", "coordinates": [mean_lng, mean_lat]},
                    properties={
                        "station": _station_name(tags["name"]),
                        "project": project,
                        "status": "under-construction",
                        "source": "OpenStreetMap contributors (ODbL)",
                    },
                )
            )
    return FeatureCollection(features=features)


# --- road-construction ------------------------------------------------------


def fetch_road_construction() -> FeatureCollection:
    under_construction = get_json(
        f"{COV_API}/road-ahead-projects-under-construction/exports/geojson"
    )
    upcoming = get_json(f"{COV_API}/road-ahead-upcoming-projects/exports/geojson")
    features = transform_roads(under_construction, "under-construction").features
    features += transform_roads(upcoming, "upcoming").features
    return FeatureCollection(features=features)


def _project_label(props: dict[str, Any]) -> str | None:
    for key in ("project", "street", "location"):
        value = props.get(key)
        if value:
            first_line = re.split(r"[\r\n]", str(value))[0]
            label = re.sub(r"\s+", " ", first_line).strip()
            if label:
                return label[:120]
    return None


def transform_roads(raw: dict[str, Any], status: str) -> FeatureCollection:
    """Road Ahead GeoJSON -> features (GeometryCollections exploded)."""
    features: list[Feature] = []
    for feature in raw.get("features", []):
        geometry = feature.get("geometry")
        props = feature.get("properties") or {}
        label = _project_label(props)
        if not geometry or not label:
            continue
        properties = {
            "project": label,
            "status": status,
            "completion": props.get("comp_date"),
            "url": props.get("url_link"),
            "source": "City of Vancouver Road Ahead",
        }
        geometries = (
            geometry["geometries"] if geometry.get("type") == "GeometryCollection" else [geometry]
        )
        features.extend(
            Feature(geometry=part, properties=dict(properties))
            for part in geometries
            if part and part.get("coordinates")
        )
    return FeatureCollection(features=features)


# --- new-highrises ----------------------------------------------------------


def fetch_new_highrises() -> FeatureCollection:
    raw = get_json(
        f"{COV_API}/issued-building-permits/exports/geojson",
        {
            "where": (
                f"typeofwork='New Building' and projectvalue>={HIGHRISE_MIN_VALUE} "
                f"and issuedate>=date'{HIGHRISE_SINCE}'"
            )
        },
    )
    return transform_permits(raw)


def transform_permits(raw: dict[str, Any]) -> FeatureCollection:
    """Issued-building-permit GeoJSON -> major residential project Points."""
    features: list[Feature] = []
    for feature in raw.get("features", []):
        geometry = feature.get("geometry")
        props = feature.get("properties") or {}
        uses = props.get("propertyuse") or []
        if not geometry or not any("Dwelling" in (use or "") for use in uses):
            continue
        description = re.sub(r"\s+", " ", str(props.get("projectdescription") or "")).strip()
        features.append(
            Feature(
                geometry=geometry,
                properties={
                    "name": props.get("address"),
                    "permit": props.get("permitnumber"),
                    "project_value": props.get("projectvalue"),
                    "issued": props.get("issuedate"),
                    "local_area": props.get("geolocalarea"),
                    "uses": ", ".join(props.get("specificusecategory") or []),
                    "description": description[:200] or None,
                    "status": "permit-issued",
                    "source": "City of Vancouver issued building permits",
                },
            )
        )
    return FeatureCollection(features=features)


# --- CLI --------------------------------------------------------------------

BUILDERS = {
    "housing-prices": fetch_housing_prices,
    "demographics": fetch_demographics,
    "skytrain-expansion": fetch_skytrain_expansion,
    "road-construction": fetch_road_construction,
    "new-highrises": fetch_new_highrises,
    "skytrain-lines": translink.fetch_skytrain_lines,
    "skytrain-stations": translink.fetch_skytrain_stations,
    "bus-routes": translink.fetch_bus_routes,
    "bus-stops": translink.fetch_bus_stops,
    "seabus-wce": translink.fetch_seabus_wce,
}


def snapshot_dir() -> Path:
    return Path(settings.data_dir) / "gva"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh GVA layer snapshots.")
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
