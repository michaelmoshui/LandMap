# Canadian Municipal Geospatial Data Portals

This document aggregates verified open data catalogs, interactive GIS mapping utilities, and spatial repositories for major metropolitan regions across Canada. 

---

## Greater Toronto Area (GTA)

### Toronto Core
*   **City of Toronto Development Activity Tracker (ArcGIS Web App)**
    *   **Description**: Interactive spatial visualization portal built on the Esri ArcGIS Experience Builder framework. Synthesizes ongoing community planning applications.
    *   **Endpoint**: [ArcGIS City of Toronto Tracker](https://arcgis.com)
*   **City of Toronto Application Information Centre (AIC)**
    *   **Description**: Public repository for historical and current granular municipal planning files, minor variance catalogs, and official plan amendment declarations.
    *   **Endpoint**: [City of Toronto AIC Portal](https://toronto.ca)

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
    *   **Endpoint**: [City of Vancouver Open Data Portal Catalog](https://vancouver.ca)
*   **City of Vancouver Issued Building Permits Map**
    *   **Description**: Mapping catalog isolating parcel-level structural adjustments, updates, and historic real estate developments.
    *   **Endpoint**: [City of Vancouver Issued Permits Map](https://vancouver.cadataset/issued-building-permits/map/)
*   **Shape Your City Vancouver**
    *   **Description**: Dynamic public consultation mapping dashboard isolating active rezoning requests and major structural development permits.
    *   **Endpoint**: [Shape Your City Vancouver Development](https://shapeyourcity.ca)

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
    *   **Endpoint**: [City of Burnaby Open Data Hub](https://data-burnaby.hub.arcgis.com/)
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
