import type { StyleSpecification } from "maplibre-gl";

// Minimal Google-Maps-like basemap: light neutral land, pale water and parks,
// white roads (yellow motorways), gray building footprints, and only the labels
// needed for orientation. Rendering a small, fixed set of vector layers keeps
// the map fast; POIs, transit, hillshading, etc. are intentionally omitted.
//
// Tiles and fonts come from OpenFreeMap (OpenMapTiles schema) - free, no API
// key, so the stack stays fully self-hostable. Swap the source `url` for a
// self-hosted tile server later without touching the layers below.
export const BASE_MAP_STYLE: StyleSpecification = {
  version: 8,
  glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
  sources: {
    openmaptiles: {
      type: "vector",
      url: "https://tiles.openfreemap.org/planet",
      attribution: "© OpenStreetMap contributors, © OpenFreeMap",
    },
  },
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#f2f1ec" },
    },
    {
      id: "landuse-developed",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "landuse",
      filter: [
        "in",
        ["get", "class"],
        ["literal", ["residential", "suburb", "neighbourhood", "commercial", "industrial"]],
      ],
      paint: { "fill-color": "#eae8e1" },
    },
    {
      id: "greenery",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "landcover",
      filter: ["in", ["get", "class"], ["literal", ["grass", "wood", "farmland", "wetland"]]],
      paint: { "fill-color": "#cfe8c4", "fill-opacity": 0.7 },
    },
    {
      id: "park",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "park",
      paint: { "fill-color": "#c5e5b9" },
    },
    {
      id: "water",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "water",
      paint: { "fill-color": "#aadaff" },
    },
    {
      id: "waterway",
      type: "line",
      source: "openmaptiles",
      "source-layer": "waterway",
      paint: { "line-color": "#aadaff", "line-width": 1.5 },
    },
    {
      id: "building",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "building",
      minzoom: 13,
      paint: {
        "fill-color": "#e3e0d8",
        "fill-outline-color": "#cfcabe",
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.6, 15, 1],
      },
    },
    {
      id: "road-minor",
      type: "line",
      source: "openmaptiles",
      "source-layer": "transportation",
      minzoom: 12,
      filter: ["in", ["get", "class"], ["literal", ["minor", "service", "track"]]],
      paint: {
        "line-color": "#ffffff",
        "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 12, 0.5, 18, 10],
      },
    },
    {
      id: "road-mid",
      type: "line",
      source: "openmaptiles",
      "source-layer": "transportation",
      filter: ["in", ["get", "class"], ["literal", ["primary", "secondary", "tertiary"]]],
      paint: {
        "line-color": "#ffffff",
        "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 8, 0.75, 18, 16],
      },
    },
    {
      id: "road-highway-casing",
      type: "line",
      source: "openmaptiles",
      "source-layer": "transportation",
      filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk"]]],
      paint: {
        "line-color": "#e9c266",
        "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 6, 2, 18, 22],
      },
    },
    {
      id: "road-highway",
      type: "line",
      source: "openmaptiles",
      "source-layer": "transportation",
      filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk"]]],
      paint: {
        "line-color": "#fcd688",
        "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 6, 1, 18, 18],
      },
    },
    {
      id: "boundary",
      type: "line",
      source: "openmaptiles",
      "source-layer": "boundary",
      filter: ["<=", ["get", "admin_level"], 4],
      paint: {
        "line-color": "#b8b3c1",
        "line-width": 1,
        "line-dasharray": [3, 2],
      },
    },
    {
      id: "road-label",
      type: "symbol",
      source: "openmaptiles",
      "source-layer": "transportation_name",
      minzoom: 14,
      layout: {
        "symbol-placement": "line",
        "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
        "text-font": ["Noto Sans Regular"],
        "text-size": 12,
      },
      paint: {
        "text-color": "#6f6f6f",
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.5,
      },
    },
    {
      id: "place-label",
      type: "symbol",
      source: "openmaptiles",
      "source-layer": "place",
      filter: ["in", ["get", "class"], ["literal", ["city", "town", "village", "suburb"]]],
      layout: {
        "text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
        "text-font": ["Noto Sans Regular"],
        "text-size": ["match", ["get", "class"], "city", 16, "town", 14, 12],
      },
      paint: {
        "text-color": "#38383d",
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.5,
      },
    },
  ],
};
