"""Unit tests for the TransLink-specific policies in app.ingest.translink.

The generic GTFS transforms are covered by ``test_ingest_gtfs.py``; these
tests pin the GVA station partition (SkyTrain vs SeaBus/WCE) and colours.
"""

from __future__ import annotations

from app.ingest import gtfs, translink

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

STOPS = [
    {
        "stop_id": "st-waterfront",
        "stop_name": "Waterfront Station",
        "stop_lat": "49.2856",
        "stop_lon": "-123.1119",
        "location_type": "1",
        "parent_station": "",
    },
    {
        "stop_id": "st-mission",
        "stop_name": "Mission City Station",
        "stop_lat": "49.1345",
        "stop_lon": "-122.3126",
        "location_type": "1",
        "parent_station": "",
    },
    {  # Platform inside a station: feeds the station index.
        "stop_id": "plat-1",
        "stop_name": "Waterfront Station @ Platform 1",
        "stop_lat": "49.2856",
        "stop_lon": "-123.1119",
        "location_type": "0",
        "parent_station": "st-waterfront",
    },
    {
        "stop_id": "plat-2",
        "stop_name": "Mission City Station @ Platform",
        "stop_lat": "49.1345",
        "stop_lon": "-122.3126",
        "location_type": "0",
        "parent_station": "st-mission",
    },
]

STOP_ROUTES = {
    "plat-1": {"expo", "seabus"},
    "plat-2": {"wce"},
}


class TestBuildStations:
    def test_partitions_skytrain_from_wce_only_stations(self) -> None:
        skytrain, other = translink.build_stations(STOPS, STOP_ROUTES, ROUTES)
        assert [f.properties["station"] for f in skytrain] == ["Waterfront Station"]
        assert [f.properties["station"] for f in other] == ["Mission City Station"]

    def test_interchanges_get_neutral_color_single_line_gets_line_color(self) -> None:
        skytrain, other = translink.build_stations(STOPS, STOP_ROUTES, ROUTES)
        waterfront = skytrain[0]
        assert waterfront.properties["lines"] == "Expo Line, SeaBus"
        assert waterfront.properties["color"] == gtfs.INTERCHANGE_COLOR
        assert other[0].properties["color"] == "#87189D"

    def test_bus_routes_never_count_as_station_lines(self) -> None:
        stop_routes = {"plat-1": {"expo", "b99"}}
        skytrain, _ = translink.build_stations(STOPS, stop_routes, ROUTES)
        waterfront = next(f for f in skytrain if f.properties["station"] == "Waterfront Station")
        assert waterfront.properties["lines"] == "Expo Line"
        assert waterfront.properties["color"] == "#0033A0"
