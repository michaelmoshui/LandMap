"""Unit tests for the pure transform functions in app.ingest.gva."""

from __future__ import annotations

from app.ingest import gva


def _way(way_id: int, tags: dict[str, str], points: list[tuple[float, float]]) -> dict:
    return {
        "type": "way",
        "id": way_id,
        "tags": tags,
        "geometry": [{"lon": lng, "lat": lat} for lng, lat in points],
    }


class TestTransformCensus:
    RAW = {
        "features": [
            {
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
                "properties": {
                    "CSDNAME": "Vancouver",
                    "CSDTYPED": "City",
                    "Population2021": 662248,
                    "Population2016": 631486,
                    "PopPctChange16to21": 4.9,
                    "TotPrivDwellings2021": 328347,
                    "PopPerSqKm2021": 5749.9,
                    "LandAreaSqKm2021": 115.18,
                },
            },
            {  # No population reported: dropped.
                "geometry": {"type": "Polygon", "coordinates": [[[2, 2], [2, 3], [3, 3], [2, 2]]]},
                "properties": {"CSDNAME": "Barnston Island 3", "Population2021": None},
            },
        ]
    }

    def test_renames_properties_and_drops_unpopulated(self) -> None:
        collection = gva.transform_census(self.RAW)
        assert len(collection.features) == 1
        props = collection.features[0].properties
        assert props["municipality"] == "Vancouver"
        assert props["population_2021"] == 662248
        assert props["density_per_km2"] == 5749.9
        assert "Statistics Canada" in props["source"]


class TestTransformOverpass:
    RAW = {
        "elements": [
            _way(
                1,
                {"railway": "construction", "construction": "subway", "opening_date": "2027"},
                [(-123.10, 49.26), (-123.12, 49.26)],
            ),
            _way(
                2,
                {"railway": "construction", "construction": "subway", "name": "SkyTrain Expo Line"},
                [(-122.85, 49.19), (-122.84, 49.18)],
            ),
            _way(
                3,
                {
                    "landuse": "construction",
                    "name": "SLS Project - Fleetwood Station Construction Area",
                },
                [(-122.78, 49.15), (-122.77, 49.16)],
            ),
            {"type": "node", "id": 4, "lat": 49.2, "lon": -123.0},  # No geometry: ignored.
        ]
    }

    def test_lines_grouped_into_projects_by_longitude(self) -> None:
        collection = gva.transform_overpass(self.RAW)
        lines = [f for f in collection.features if f.geometry["type"] == "LineString"]
        assert [f.properties["project"] for f in lines] == [
            "Millennium Line Broadway Extension",
            "Surrey-Langley SkyTrain",
        ]
        assert lines[0].properties["opens"] == "2027"
        assert lines[0].geometry["coordinates"] == [[-123.10, 49.26], [-123.12, 49.26]]
        assert all(f.properties["status"] == "under-construction" for f in lines)

    def test_station_sites_become_named_points(self) -> None:
        collection = gva.transform_overpass(self.RAW)
        stations = [f for f in collection.features if f.geometry["type"] == "Point"]
        assert len(stations) == 1
        assert stations[0].properties["station"] == "Fleetwood Station"
        assert stations[0].properties["project"] == "Surrey-Langley SkyTrain"
        lng, lat = stations[0].geometry["coordinates"]
        assert -122.79 < lng < -122.76 and 49.14 < lat < 49.17

    def test_station_name_cleanup(self) -> None:
        cleaned = gva._station_name("South Granville Station Construction")
        assert cleaned == "South Granville Station"
        assert gva._station_name("SLS - Green Timbers Station") == "Green Timbers Station"
        assert (
            gva._station_name("Surrey Langley SkyTrain Project - Willowbrook Station")
            == "Willowbrook Station"
        )


class TestTransformRoads:
    RAW = {
        "features": [
            {
                "geometry": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {"type": "LineString", "coordinates": [[-123.1, 49.2], [-123.1, 49.3]]},
                        {"type": "LineString", "coordinates": [[-123.2, 49.2], [-123.2, 49.3]]},
                    ],
                },
                "properties": {
                    "project": "900\tRenfrew St - E\r\nsecond line ignored",
                    "comp_date": "2026-08-02",
                    "url_link": "https://vancouver.ca/roadahead",
                },
            },
            {
                "geometry": {"type": "LineString", "coordinates": [[-123.0, 49.2], [-123.0, 49.3]]},
                "properties": {"project": None, "street": "Main St", "comp_date": None},
            },
            {  # No geometry: dropped.
                "geometry": None,
                "properties": {"project": "Ghost project"},
            },
        ]
    }

    def test_explodes_geometry_collections_and_cleans_labels(self) -> None:
        collection = gva.transform_roads(self.RAW, "under-construction")
        assert len(collection.features) == 3
        first, second, third = collection.features
        assert first.properties["project"] == "900 Renfrew St - E"
        assert first.geometry["type"] == "LineString"
        assert second.properties["project"] == first.properties["project"]
        assert third.properties["project"] == "Main St"
        assert all(f.properties["status"] == "under-construction" for f in collection.features)


class TestTransformPermits:
    RAW = {
        "features": [
            {
                "geometry": {"type": "Point", "coordinates": [-123.03, 49.23]},
                "properties": {
                    "address": "3380 VANNESS AVENUE, Vancouver, BC",
                    "permitnumber": "BP-2026-00001",
                    "projectvalue": 144787150.0,
                    "issuedate": "2026-03-19",
                    "geolocalarea": "Renfrew-Collingwood",
                    "propertyuse": ["Dwelling Uses", "Retail Uses"],
                    "specificusecategory": ["Dwelling Unit", "Retail Store"],
                    "projectdescription": "New  38-storey\r\nmixed-use building",
                },
            },
            {  # Office-only: not housing.
                "geometry": {"type": "Point", "coordinates": [-123.1, 49.28]},
                "properties": {"address": "OFFICE ST", "propertyuse": ["Office Uses"]},
            },
            {  # No geometry: dropped.
                "geometry": None,
                "properties": {"address": "NOWHERE", "propertyuse": ["Dwelling Uses"]},
            },
        ]
    }

    def test_keeps_geolocated_residential_permits(self) -> None:
        collection = gva.transform_permits(self.RAW)
        assert len(collection.features) == 1
        props = collection.features[0].properties
        assert props["name"] == "3380 VANNESS AVENUE, Vancouver, BC"
        assert props["project_value"] == 144787150.0
        assert props["description"] == "New 38-storey mixed-use building"
        assert props["uses"] == "Dwelling Unit, Retail Store"


class TestMergeHousing:
    BOUNDARIES = {
        "features": [
            {
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
                "properties": {"name": "Downtown"},
            },
            {
                "geometry": {"type": "Polygon", "coordinates": [[[2, 2], [2, 3], [3, 3], [2, 2]]]},
                "properties": {"name": "Oakridge"},
            },
        ]
    }
    CODE_STATS = {
        "STRATA": {
            "001": {"n": 100, "avg_value": 800_000.0},
            "002": {"n": 300, "avg_value": 1_000_000.0},
            "003": {"n": 50, "avg_value": 2_000_000.0},
        },
        "LAND": {"003": {"n": 20, "avg_value": 3_000_000.0}},
    }
    CODE_TO_AREA = {"001": "Downtown", "002": "Downtown", "003": None}

    def test_weighted_average_per_area(self) -> None:
        collection = gva.merge_housing(self.BOUNDARIES, self.CODE_STATS, self.CODE_TO_AREA, "2026")
        by_area = {f.properties["area"]: f.properties for f in collection.features}
        assert set(by_area) == {"Downtown", "Oakridge"}
        downtown = by_area["Downtown"]
        # (100*800k + 300*1M) / 400 = 950k; code 003 is unmapped and excluded.
        assert downtown["strata_avg_value"] == 950_000
        assert downtown["strata_count"] == 400
        assert downtown["land_avg_value"] is None
        assert downtown["assessment_year"] == "2026"
        # Areas without data still render, with empty stats.
        assert by_area["Oakridge"]["strata_count"] == 0
