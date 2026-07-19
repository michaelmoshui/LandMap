"""Unit tests for the generic GTFS transforms in app.ingest.gtfs."""

from __future__ import annotations

import pytest

from app.ingest import gtfs

DEFAULT_COLOR = "#7A99AC"
SOURCE = "Test GTFS feed"

ROUTES = [
    {
        "route_id": "expo",
        "route_short_name": "",
        "route_long_name": "Expo Line",
        "route_type": "1",
        "route_color": "0033a0",
    },
    {
        "route_id": "b99",
        "route_short_name": "099",
        "route_long_name": "Broadway B-Line",
        "route_type": "3",
        "route_color": "d04110",
    },
    {
        "route_id": "local",
        "route_short_name": "025",
        "route_long_name": "Brentwood Station/UBC",
        "route_type": "3",
        "route_color": "",
    },
    {
        "route_id": "wce",
        "route_short_name": "WCE",
        "route_long_name": "West Coast Express",
        "route_type": "2",
        "route_color": "87189d",
    },
]

TRIPS = [
    # Expo Line: two shape variants (branches) in the same direction.
    {"route_id": "expo", "trip_id": "e1", "direction_id": "0", "shape_id": "expo-a"},
    {"route_id": "expo", "trip_id": "e2", "direction_id": "0", "shape_id": "expo-b"},
    # 99: shape "b99-main" is busiest in direction 0; "b99-short" must lose.
    {"route_id": "b99", "trip_id": "t1", "direction_id": "0", "shape_id": "b99-main"},
    {"route_id": "b99", "trip_id": "t2", "direction_id": "0", "shape_id": "b99-main"},
    {"route_id": "b99", "trip_id": "t3", "direction_id": "0", "shape_id": "b99-short"},
    {"route_id": "b99", "trip_id": "t4", "direction_id": "1", "shape_id": "b99-back"},
    {"route_id": "local", "trip_id": "l1", "direction_id": "0", "shape_id": "local-a"},
]

SHAPES = {
    "expo-a": [[-123.11, 49.28], [-123.01, 49.22]],
    "expo-b": [[-123.01, 49.22], [-122.85, 49.22]],
    "b99-main": [[-123.11, 49.26], [-123.05, 49.26], [-122.99, 49.26]],
    "b99-short": [[-123.11, 49.26], [-123.05, 49.26]],
    "b99-back": [[-122.99, 49.263], [-123.11, 49.263]],
    "local-a": [[-123.20, 49.26], [-123.00, 49.25]],
}

_MODES = {"1": "SkyTrain", "2": "Commuter Rail", "3": "Bus"}


def _mode_for(route: dict[str, str]) -> str:
    return _MODES.get(route["route_type"], "Transit")


def _bus_lines(**kwargs: object) -> list:
    return gtfs.build_route_lines(
        ROUTES,
        TRIPS,
        SHAPES,
        route_ids={"b99", "local"},
        mode_for=_mode_for,
        default_color=DEFAULT_COLOR,
        source=SOURCE,
        **kwargs,  # type: ignore[arg-type]
    )


class TestRouteHelpers:
    def test_color_uses_official_agency_hex(self) -> None:
        assert gtfs.route_color(ROUTES[0], DEFAULT_COLOR) == "#0033A0"

    def test_colorless_routes_fall_back_to_the_default(self) -> None:
        assert gtfs.route_color(ROUTES[2], DEFAULT_COLOR) == DEFAULT_COLOR

    def test_label_strips_leading_zeros_and_falls_back_to_long_name(self) -> None:
        assert gtfs.route_label(ROUTES[1]) == "99"
        assert gtfs.route_label(ROUTES[0]) == "Expo Line"


class TestSimplifyLine:
    def test_drops_collinear_and_duplicate_points_keeps_corners(self) -> None:
        line = [
            [-123.10, 49.20],
            [-123.10, 49.20],  # duplicate
            [-123.09, 49.20],  # collinear
            [-123.08, 49.20],  # corner
            [-123.08, 49.25],
        ]
        assert gtfs.simplify_line(line) == [
            [-123.10, 49.20],
            [-123.08, 49.20],
            [-123.08, 49.25],
        ]

    def test_endpoints_always_survive(self) -> None:
        line = [[-123.0, 49.0], [-122.9, 49.1]]
        assert gtfs.simplify_line(line) == line


class TestBuildRouteLines:
    def test_keeps_only_the_busiest_shape_per_direction(self) -> None:
        features = _bus_lines()
        b99 = [f for f in features if f.properties["route"] == "99"]
        coords = {tuple(map(tuple, f.geometry["coordinates"])) for f in b99}
        assert len(b99) == 2  # one per direction; the short-turn variant lost
        assert tuple(map(tuple, SHAPES["b99-short"])) not in coords

    def test_all_variants_keeps_every_branch(self) -> None:
        features = gtfs.build_route_lines(
            ROUTES,
            TRIPS,
            SHAPES,
            route_ids={"expo"},
            mode_for=_mode_for,
            default_color=DEFAULT_COLOR,
            source=SOURCE,
            all_variants=True,
        )
        assert len(features) == 2
        assert all(f.properties["color"] == "#0033A0" for f in features)
        assert all(f.properties["mode"] == "SkyTrain" for f in features)

    def test_properties_carry_names_and_source(self) -> None:
        b99 = next(f for f in _bus_lines() if f.properties["route"] == "99")
        assert b99.properties["name"] == "Broadway B-Line"
        assert b99.properties["color"] == "#D04110"
        assert b99.properties["source"] == SOURCE

    def test_custom_label_policy_wins(self) -> None:
        features = _bus_lines(label_for=lambda r: r["route_long_name"])
        assert {f.properties["route"] for f in features} == {
            "Broadway B-Line",
            "Brentwood Station/UBC",
        }


class TestStationFeature:
    def test_single_line_station_wears_the_line_color(self) -> None:
        feature = gtfs.station_feature(
            "Mission City Station",
            [-122.3126, 49.1345],
            [ROUTES[3]],
            default_color=DEFAULT_COLOR,
            source=SOURCE,
        )
        assert feature.properties["lines"] == "WCE"  # default label: short name
        assert feature.properties["color"] == "#87189D"

    def test_interchanges_get_the_neutral_ring(self) -> None:
        feature = gtfs.station_feature(
            "Waterfront Station",
            [-123.1119, 49.2856],
            [ROUTES[0], ROUTES[3]],
            default_color=DEFAULT_COLOR,
            source=SOURCE,
        )
        assert feature.properties["lines"] == "Expo Line, WCE"
        assert feature.properties["color"] == gtfs.INTERCHANGE_COLOR


class TestBuildStationsFromStops:
    STOPS = [
        {
            "stop_id": "p1",
            "stop_name": "Bay Station - Eastbound Platform",
            "stop_lat": "43.6700",
            "stop_lon": "-79.3900",
            "location_type": "",
            "parent_station": "",
        },
        {
            "stop_id": "p2",
            "stop_name": "Bay Station - Westbound Platform",
            "stop_lat": "43.6710",
            "stop_lon": "-79.3910",
            "location_type": "",
            "parent_station": "",
        },
        {
            "stop_id": "b1",
            "stop_name": "Bay St @ Bloor St",
            "stop_lat": "43.6690",
            "stop_lon": "-79.3890",
            "location_type": "",
            "parent_station": "",
        },
    ]

    def test_groups_platforms_by_cleaned_name_at_their_centroid(self) -> None:
        import re

        clean = lambda name: re.sub(r"\s*-\s*\w+bound Platform$", "", name)  # noqa: E731
        features = gtfs.build_stations_from_stops(
            self.STOPS,
            {"p1": {"expo"}, "p2": {"expo"}, "b1": {"local"}},
            ROUTES,
            line_ids={"expo"},
            clean_name=clean,
            default_color=DEFAULT_COLOR,
            source=SOURCE,
        )
        assert len(features) == 1  # the bus stop never becomes a station
        station = features[0]
        assert station.properties["station"] == "Bay Station"
        assert station.geometry["coordinates"] == pytest.approx([-79.3905, 43.6705])
        assert station.properties["lines"] == "Expo Line"


class TestBuildBusStops:
    STOPS = [
        {
            "stop_id": "bus-1",
            "stop_name": "W Broadway @ Cambie St",
            "stop_lat": "49.2634",
            "stop_lon": "-123.1140",
            "location_type": "0",
            "parent_station": "",
            "stop_code": "50791",
        },
        {  # Platform of a parent station: excluded.
            "stop_id": "plat-1",
            "stop_name": "Waterfront Station @ Platform 1",
            "stop_lat": "49.2856",
            "stop_lon": "-123.1119",
            "location_type": "0",
            "parent_station": "st-waterfront",
            "stop_code": "",
        },
        {  # Parentless rail platform (TTC-style): serves no surface route.
            "stop_id": "plat-2",
            "stop_name": "Bay Station - Eastbound Platform",
            "stop_lat": "43.6700",
            "stop_lon": "-79.3900",
            "location_type": "",
            "parent_station": "",
            "stop_code": "",
        },
        {  # Station record itself: excluded by location_type.
            "stop_id": "st-waterfront",
            "stop_name": "Waterfront Station",
            "stop_lat": "49.2856",
            "stop_lon": "-123.1119",
            "location_type": "1",
            "parent_station": "",
            "stop_code": "",
        },
    ]

    STOP_ROUTES = {"bus-1": {"b99", "local"}, "plat-1": {"expo"}, "plat-2": {"expo"}}

    def _stops(self) -> list:
        return gtfs.build_bus_stops(
            self.STOPS,
            self.STOP_ROUTES,
            ROUTES,
            surface_ids={"b99", "local"},
            source=SOURCE,
        )

    def test_excludes_platforms_and_stations(self) -> None:
        assert [f.properties["stop"] for f in self._stops()] == ["W Broadway @ Cambie St"]

    def test_lists_serving_routes_in_rider_order(self) -> None:
        stop = self._stops()[0]
        assert stop.properties["routes"] == "25, 99"
        assert stop.properties["code"] == "50791"
        assert stop.geometry["coordinates"] == [-123.1140, 49.2634]
