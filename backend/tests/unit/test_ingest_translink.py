"""Unit tests for the pure transform functions in app.ingest.translink."""

from __future__ import annotations

from app.ingest import translink

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
    {
        "route_id": "seabus",
        "route_short_name": "",
        "route_long_name": "SeaBus",
        "route_type": "4",
        "route_color": "746661",
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

STOPS = [
    {
        "stop_id": "st-waterfront",
        "stop_name": "Waterfront Station",
        "stop_lat": "49.2856",
        "stop_lon": "-123.1119",
        "location_type": "1",
        "parent_station": "",
        "stop_code": "",
    },
    {
        "stop_id": "st-mission",
        "stop_name": "Mission City Station",
        "stop_lat": "49.1345",
        "stop_lon": "-122.3126",
        "location_type": "1",
        "parent_station": "",
        "stop_code": "",
    },
    {  # Platform inside a station: feeds the station index, not bus stops.
        "stop_id": "plat-1",
        "stop_name": "Waterfront Station @ Platform 1",
        "stop_lat": "49.2856",
        "stop_lon": "-123.1119",
        "location_type": "0",
        "parent_station": "st-waterfront",
        "stop_code": "",
    },
    {
        "stop_id": "plat-2",
        "stop_name": "Mission City Station @ Platform",
        "stop_lat": "49.1345",
        "stop_lon": "-122.3126",
        "location_type": "0",
        "parent_station": "st-mission",
        "stop_code": "",
    },
    {
        "stop_id": "bus-1",
        "stop_name": "W Broadway @ Cambie St",
        "stop_lat": "49.2634",
        "stop_lon": "-123.1140",
        "location_type": "0",
        "parent_station": "",
        "stop_code": "50791",
    },
    {  # Station entrance: neither a station nor a bus stop.
        "stop_id": "door-1",
        "stop_name": "Waterfront Station Entrance",
        "stop_lat": "49.2856",
        "stop_lon": "-123.1119",
        "location_type": "2",
        "parent_station": "st-waterfront",
        "stop_code": "",
    },
]

STOP_ROUTES = {
    "plat-1": {"expo", "seabus"},
    "plat-2": {"wce"},
    "bus-1": {"b99", "local"},
}


class TestRouteHelpers:
    def test_color_uses_official_translink_hex(self) -> None:
        assert translink.route_color(ROUTES[0]) == "#0033A0"

    def test_colorless_local_buses_fall_back_to_system_map_gray_blue(self) -> None:
        assert translink.route_color(ROUTES[2]) == translink.DEFAULT_BUS_COLOR

    def test_label_strips_leading_zeros_and_falls_back_to_long_name(self) -> None:
        assert translink.route_label(ROUTES[1]) == "99"
        assert translink.route_label(ROUTES[0]) == "Expo Line"


class TestSimplifyLine:
    def test_drops_collinear_and_duplicate_points_keeps_corners(self) -> None:
        line = [
            [-123.10, 49.20],
            [-123.10, 49.20],  # duplicate
            [-123.09, 49.20],  # collinear
            [-123.08, 49.20],  # corner
            [-123.08, 49.25],
        ]
        assert translink.simplify_line(line) == [
            [-123.10, 49.20],
            [-123.08, 49.20],
            [-123.08, 49.25],
        ]

    def test_endpoints_always_survive(self) -> None:
        line = [[-123.0, 49.0], [-122.9, 49.1]]
        assert translink.simplify_line(line) == line


class TestBuildRouteLines:
    def test_buses_keep_only_the_busiest_shape_per_direction(self) -> None:
        features = translink.build_route_lines(ROUTES, TRIPS, SHAPES, route_types={translink.BUS})
        b99 = [f for f in features if f.properties["route"] == "99"]
        coords = {tuple(map(tuple, f.geometry["coordinates"])) for f in b99}
        assert len(b99) == 2  # one per direction; the short-turn variant lost
        assert tuple(map(tuple, SHAPES["b99-short"])) not in coords

    def test_rail_keeps_every_branch_variant(self) -> None:
        features = translink.build_route_lines(
            ROUTES, TRIPS, SHAPES, route_types={translink.SKYTRAIN}, all_variants=True
        )
        assert len(features) == 2
        assert all(f.properties["color"] == "#0033A0" for f in features)
        assert all(f.properties["mode"] == "SkyTrain" for f in features)

    def test_properties_carry_names_and_source(self) -> None:
        features = translink.build_route_lines(ROUTES, TRIPS, SHAPES, route_types={translink.BUS})
        b99 = next(f for f in features if f.properties["route"] == "99")
        assert b99.properties["name"] == "Broadway B-Line"
        assert b99.properties["color"] == "#D04110"
        assert b99.properties["source"] == translink.SOURCE


class TestBuildStations:
    def test_partitions_skytrain_from_wce_only_stations(self) -> None:
        skytrain, other = translink.build_stations(STOPS, STOP_ROUTES, ROUTES)
        assert [f.properties["station"] for f in skytrain] == ["Waterfront Station"]
        assert [f.properties["station"] for f in other] == ["Mission City Station"]

    def test_interchanges_get_neutral_color_single_line_gets_line_color(self) -> None:
        skytrain, other = translink.build_stations(STOPS, STOP_ROUTES, ROUTES)
        waterfront = skytrain[0]
        assert waterfront.properties["lines"] == "Expo Line, SeaBus"
        assert waterfront.properties["color"] == translink.INTERCHANGE_COLOR
        assert other[0].properties["color"] == "#87189D"

    def test_bus_routes_never_count_as_station_lines(self) -> None:
        stop_routes = {"plat-1": {"expo", "b99"}}
        skytrain, _ = translink.build_stations(STOPS, stop_routes, ROUTES)
        waterfront = next(f for f in skytrain if f.properties["station"] == "Waterfront Station")
        assert waterfront.properties["lines"] == "Expo Line"
        assert waterfront.properties["color"] == "#0033A0"


class TestBuildBusStops:
    def test_excludes_platforms_entrances_and_stations(self) -> None:
        features = translink.build_bus_stops(STOPS, STOP_ROUTES, ROUTES)
        assert [f.properties["stop"] for f in features] == ["W Broadway @ Cambie St"]

    def test_lists_serving_bus_routes_in_rider_order(self) -> None:
        features = translink.build_bus_stops(STOPS, STOP_ROUTES, ROUTES)
        stop = features[0]
        assert stop.properties["routes"] == "25, 99"
        assert stop.properties["code"] == "50791"
        assert stop.geometry["coordinates"] == [-123.1140, 49.2634]
