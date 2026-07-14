import type { StyleSpecification } from "maplibre-gl";

// Minimal greyscale basemap (Uber-style): light grey land, darker grey water,
// white roads, grey building footprints, and only the labels needed for
// orientation. Everything is monochrome so data overlays carry all the color.
// Rendering a small, fixed set of vector layers keeps the map fast; POIs,
// transit, hillshading, etc. are intentionally omitted.
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
      paint: { "background-color": "#ebebeb" },
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
      paint: { "fill-color": "#e4e4e4" },
    },
    {
      id: "greenery",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "landcover",
      filter: ["in", ["get", "class"], ["literal", ["grass", "wood", "farmland", "wetland"]]],
      paint: { "fill-color": "#e0e0e0", "fill-opacity": 0.7 },
    },
    {
      id: "park",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "park",
      paint: { "fill-color": "#dcdcdc" },
    },
    {
      id: "water",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "water",
      paint: { "fill-color": "#acc4c5" },
    },
    {
      id: "waterway",
      type: "line",
      source: "openmaptiles",
      "source-layer": "waterway",
      paint: { "line-color": "#c9c9c9", "line-width": 1.5 },
    },
    {
      id: "building",
      type: "fill",
      source: "openmaptiles",
      "source-layer": "building",
      minzoom: 13,
      paint: {
        "fill-color": "#dfdfdf",
        "fill-outline-color": "#cccccc",
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
        "line-color": "#eeeeee",
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
        "line-color": "#e0e0e0",
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
        "line-color": "#d5d5d5",
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
        "line-color": "#b5b5b5",
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
        "text-color": "#757575",
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
        "text-color": "#4a4a4a",
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.5,
      },
    },
  ],
};
