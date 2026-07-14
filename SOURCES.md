# Canadian Municipal Geospatial Data Portals

This document aggregates open data catalogs, interactive GIS mapping utilities, and spatial repositories for major metropolitan regions across Canada. Entries are starting points, not all individually verified; the exception is the "Endpoints used by LandMap" section below, whose URLs are verified programmatic endpoints.

---

## Greater Toronto Area (GTA)

### Toronto Core
*   **City of Toronto Development Activity Tracker (ArcGIS Web App)**
    *   **Description**: Interactive spatial visualization portal built on the Esri ArcGIS Experience Builder framework. Synthesizes ongoing community planning applications.
    *   **Endpoint**: [ArcGIS City of Toronto Tracker](https://arcgis.com)
*   **City of Toronto Application Information Centre (AIC)**
    *   **Description**: Public repository for historical and current granular municipal planning files, minor variance catalogs, and official plan amendment declarations.
    *   **Endpoint**: [City of Toronto AIC Portal](https://toronto.ca)

### Transit Agency Feeds
*   **TTC GTFS Static Feed**
    *   **Description**: The complete TTC network (subway/LRT Lines 1-6, streetcars, buses, stops and the TTC's official route colours) as a GTFS zip from Toronto Open Data. Feeds the GTA `gta-subway-lines`, `gta-subway-stations`, `gta-streetcar-lines`, `gta-bus-routes`, and `gta-bus-stops` layers.
    *   **Endpoint**: [TTC Routes and Schedules (GTFS)](http://opendata.toronto.ca/toronto.transit.commission/ttc-routes-and-schedules/OpenData_TTC_Schedules.zip)
*   **GO Transit GTFS Static Feed (Metrolinx)**
    *   **Description**: GO train and bus network (routes, shapes, stations and Metrolinx's official line colours) as a GTFS zip. Feeds the GTA `gta-go-transit` layer (rail only).
    *   **Endpoint**: [GO Transit GTFS](https://assets.metrolinx.com/raw/upload/Documents/Metrolinx/Open%20Data/GO-GTFS.zip)

### Regional Portals & Community Alternatives
*   **York Region Development Application Dashboard**
    *   **Description**: Unified Esri operations dashboard logging development boundaries, review stages, and processing metrics across northern regional municipalities (Vaughan, Markham, Richmond Hill).
    *   **Endpoint**: [ArcGIS York Region Dashboard](https://arcgis.com)
*   **UrbanToronto Interactive Map**
    *   **Description**: Third-party private commercial real estate and high-density development index maps, bridging vector density clusters directly to architectural blueprint archives.
    *   **Endpoint**: [UrbanToronto Map](https://urbantoronto.ca)

---

## Greater Vancouver Area (GVA) / Lower Mainland

### Regional & Core Hubs
*   **Metro Vancouver Regional Open Data Portal**
    *   **Description**: Consolidated regional ArcGIS Hub hosting cross-jurisdictional geographic data, containing regional transit layers, utility trunk geometry, and general land-use classification schema.
    *   **Endpoint**: [Metro Vancouver Open Data Portal](https://open-data-portal-metrovancouver.hub.arcgis.com/)
*   **City of Vancouver Open Data Portal**
    *   **Description**: High-fidelity data repository operating on the *Opendatasoft* engine. Facilitates programmatic schema extraction via direct REST APIs, CSV pipelines, or static GeoJSON arrays.
    *   **Endpoint**: [City of Vancouver Open Data Portal Catalog](https://opendata.vancouver.ca/)
*   **City of Vancouver Issued Building Permits Map**
    *   **Description**: Mapping catalog isolating parcel-level structural adjustments, updates, and historic real estate developments.
    *   **Endpoint**: [City of Vancouver Issued Permits Map](https://opendata.vancouver.ca/explore/dataset/issued-building-permits/map/)
*   **Shape Your City Vancouver**
    *   **Description**: Dynamic public consultation mapping dashboard isolating active rezoning requests and major structural development permits.
    *   **Endpoint**: [Shape Your City Vancouver Development](https://shapeyourcity.ca)

### Federal & Community Data
*   **Statistics Canada 2021 Census (via Esri Canada FeatureServer)**
    *   **Description**: Population and dwelling counts per census subdivision, republished by Esri Canada as a queryable public ArcGIS FeatureServer. Feeds the GVA `demographics` layer (Metro Vancouver CSDs, `CSDUID LIKE '5915%'`).
    *   **Endpoint**: [Canadian Population and Dwelling Counts 2021](https://services.arcgis.com/wjcPoefzjpzCgffS/arcgis/rest/services/Canadian_Population_and_Dwelling_Counts_2021/FeatureServer)
*   **TransLink GTFS Static Feed**
    *   **Description**: The complete Metro Vancouver transit network (routes, shapes, stops, stations and TransLink's official route colours) as a GTFS zip, refreshed with each service change. Feeds the GVA `skytrain-lines`, `skytrain-stations`, `bus-routes`, `bus-stops`, and `seabus-wce` layers.
    *   **Endpoint**: [TransLink GTFS Static](https://gtfs-static.translink.ca/gtfs/google_transit.zip)
*   **OpenStreetMap (Overpass API)**
    *   **Description**: Community-maintained geodata under ODbL. Carries the under-construction SkyTrain alignments and station sites (Broadway Extension, Surrey-Langley) that no government portal exposes as open GIS layers; queried via Overpass. Feeds the GVA `skytrain-expansion` layer.
    *   **Endpoint**: [Overpass API](https://overpass-api.de/api/interpreter)

### The Tri-Cities
*   **City of Coquitlam Open Data Catalog**
    *   **Description**: Native web spatial catalogue hosting discrete datasets for regional property divisions, infrastructure vectors, and topography.
    *   **Endpoint**: [Coquitlam Open Data Catalog](https://data.coquitlam.ca/)
*   **City of Port Coquitlam Open Data Hub**
    *   **Description**: Standardized Esri ArcGIS Hub serving property polygons, zoning regulations, and physical infrastructure vectors.
    *   **Endpoint**: [Port Coquitlam Open Data Hub](https://data-poco.hub.arcgis.com/)
*   **City of Port Moody Open Data Portal**
    *   **Description**: Dedicated spatial portal mapping municipal layout tables, utility structures, and city planning applications.
    *   **Endpoint**: [Port Moody Open Data](https://data.portmoody.ca/)

### The North Shore
*   **District of North Vancouver (GEOweb)**
    *   **Description**: Advanced municipal GIS repository providing direct downloads for over 170 individual spatial datasets, including weekly updated infrastructure, zoning, and contour layers.
    *   **Endpoint**: [GEOweb Open Data Portal](https://geoweb.dnv.org/data/)
*   **City of North Vancouver Map Catalog & Interactive GIS**
    *   **Description**: Specialized property lines, Lonsdale urban corridor planning datasets, and independent municipal layout dimensions.
    *   **Endpoint**: [CityMap - City of North Vancouver](https://gisext2.cnv.org/citymap/)

### Inner Metro & Eastern Lower Mainland
*   **City of Burnaby Open Data Hub**
    *   **Description**: Native ArcGIS Hub publishing precise geometric layers for legal land parcels, public works, and CAD-compatible engineering grids.
    *   **Endpoint**: [City of Burnaby Open Data Hub](https://data.burnaby.ca/)
        (the previously listed `data-burnaby.hub.arcgis.com` hostname no longer exists)
*   **City of Surrey Open Data Portal**
    *   **Description**: Core repository serving detailed real estate files, transportation layout vectors, and asset matrices for the Surrey municipality.
    *   **Endpoint**: [City of Surrey Open Data](https://surrey.ca)
*   **City of Richmond Interactive Map & GIS Repository**
    *   **Description**: Spatial portal heavily prioritized toward floodplain defenses, drainage network structures, and municipal perimeter grids.
    *   **Endpoint**: [City of Richmond Interactive Maps](https://www.richmond.ca/services/digital/maps.htm)
*   **City of Delta Open Data Hub**
    *   **Description**: ArcGIS-driven user interface exposing local infrastructure schemas, engineering networks, and layout matrices.
    *   **Endpoint**: [Delta Open Data Hub](https://opendata-deltabc.hub.arcgis.com/)
*   **Township of Langley Open Data Portal**
    *   **Description**: Spatial database organizing industrial land use distributions, rural property parceling, and agricultural boundaries.
    *   **Endpoint**: [Township of Langley Open Data Portal](https://data-tol.hub.arcgis.com/)
*   **City of Abbotsford Open Data Hub**
    *   **Description**: Specialized spatial interface optimized for downloading agricultural terrain divisions and regional land-use vectors.
    *   **Endpoint**: [Abbotsford Open Data Hub](https://data-abbotsford.hub.arcgis.com/)
*   **City of Chilliwack Open Data Portal**
    *   **Description**: Public file hierarchy serving community engineering plans, infrastructure lines, and layout vectors.
    *   **Endpoint**: [Chilliwack Open Data Portal](https://data-chilliwack.hub.arcgis.com/)

---

## Endpoints used by LandMap (verified 2026-07-13)

Consumed by `backend/app/ingest/boundaries.py` (`make ingest-boundaries`); all
return WGS84 GeoJSON with no API key:

*   **Municipalities** - Metro Vancouver Open Data, "Administrative Boundaries"
    (layer 10): `https://services6.arcgis.com/56eqCzQ5SZhBaDST/arcgis/rest/services/Administrative_Boundaries/FeatureServer/10/query?where=1%3D1&outFields=FullName,ShortName&f=geojson&outSR=4326`
*   **Vancouver neighborhoods** - City of Vancouver, "local-area-boundary":
    `https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/local-area-boundary/exports/geojson`
*   **Burnaby neighborhoods** - City of Burnaby, "Community Plan Area Boundaries"
    (layer 10): `https://gis.burnaby.ca/arcgis/rest/services/OpenData/OpenData1/MapServer/10/query?where=1%3D1&outFields=AREA_NAME&f=geojson&outSR=4326`

Neighborhood polygons for the remaining municipalities are published per-city
(see the portals above); wire them into the ingest script the same way.

---

## Programmatic Access Protocols (GIS Systems Integration)

For automated programmatic parsing or streaming of layers into GIS software (e.g., QGIS, ArcGIS Pro, Python `GeoPandas`), locate the **API Explorer** or **Developer API** metadata sub-section nested inside the target **ArcGIS Hub** dataset views.

### Integration Signatures

#### QGIS Data Source Manager Connection
*   **Protocol Type**: `ArcGIS FeatureServer` or `ArcGIS MapServer`
*   **Action**: Copy the raw base string up to the trailing operational index (e.g., `.../FeatureServer/0`) and register it directly into the GIS workspace connection array.

#### Python / GeoPandas REST Ingestion Paradigm
```python
import geopandas as gpd

# Target vector stream endpoint example
arcgis_rest_url = "https://{MUNICIPAL_SERVER_HOST}/arcgis/rest/services/{LAYER_PATH}/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"

# Stream directly into memory block as a GeoDataFrame object
gdf = gpd.read_file(arcgis_rest_url)
print(gdf.head())
```
