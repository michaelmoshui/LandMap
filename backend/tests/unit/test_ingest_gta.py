"""Unit tests for the TTC/GO-specific policies in app.ingest.gta.

The generic GTFS transforms are covered by ``test_ingest_gtfs.py``; these
tests pin the TTC route classification and station-name cleaning.
"""

from __future__ import annotations

from app.ingest import gta

ROUTES = [
    {
        "route_id": "1",
        "route_short_name": "1",
        "route_long_name": "Line 1 (Yonge-University)",
        "route_type": "1",
        "route_color": "D5C82B",
    },
    {
        "route_id": "5",
        "route_short_name": "5",
        "route_long_name": "Line 5 Eglinton",
        "route_type": "0",
        "route_color": "FF8000",
    },
    {
        "route_id": "501",
        "route_short_name": "501",
        "route_long_name": "Queen",
        "route_type": "0",
        "route_color": "ED1C24",
    },
    {
        "route_id": "301",
        "route_short_name": "301",
        "route_long_name": "Queen",
        "route_type": "0",
        "route_color": "0054A6",
    },
    {
        "route_id": "97",
        "route_short_name": "97",
        "route_long_name": "Yonge",
        "route_type": "3",
        "route_color": "ED1C24",
    },
]


class TestRouteClassification:
    def test_rapid_transit_covers_the_subway_and_single_digit_lrt_lines(self) -> None:
        assert gta.rapid_transit_ids(ROUTES) == {"1", "5"}

    def test_streetcars_are_the_remaining_trams(self) -> None:
        assert gta.streetcar_ids(ROUTES) == {"501", "301"}

    def test_mode_labels(self) -> None:
        modes = {r["route_id"]: gta.ttc_mode(r) for r in ROUTES}
        assert modes == {
            "1": "Subway",
            "5": "LRT",
            "501": "Streetcar",
            "301": "Streetcar",
            "97": "Bus",
        }


class TestNaming:
    def test_platform_suffixes_are_stripped_from_station_names(self) -> None:
        assert gta.clean_station_name("Bay Station - Eastbound Platform") == "Bay Station"
        assert gta.clean_station_name("Mount Dennis Station Westbound Platform") == (
            "Mount Dennis Station"
        )
        assert gta.clean_station_name("Union Station - Northbound Platform Towards Finch") == (
            "Union Station"
        )
        assert gta.clean_station_name("Kennedy Station - Subway Platform") == "Kennedy Station"
        assert gta.clean_station_name("Mount Dennis Station LRT Platform") == (
            "Mount Dennis Station"
        )
        assert gta.clean_station_name("Union Station GO") == "Union Station GO"

    def test_rail_lines_use_their_long_names(self) -> None:
        assert gta.line_label(ROUTES[0]) == "Line 1 (Yonge-University)"
        assert gta.line_label({"route_short_name": "LW", "route_long_name": "Lakeshore West"}) == (
            "Lakeshore West"
        )
