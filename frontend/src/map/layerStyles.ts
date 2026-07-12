import type { LayerCategory } from "../api/types";

// Color used to render each layer's features on the map.
export const CATEGORY_COLORS: Record<LayerCategory, string> = {
  baseline: "#2563eb",
  planned: "#dc2626",
};

export function colorForCategory(category: LayerCategory): string {
  return CATEGORY_COLORS[category];
}

// The Greater Vancouver Area viewport.
export const VANCOUVER_CENTER: [number, number] = [-123.02, 49.24];
export const DEFAULT_ZOOM = 10.5;

// A free raster style using OpenStreetMap tiles - no API key required, so the
// stack stays fully self-hostable. Swap for a self-hosted vector tile server
// later if desired.
export const OSM_STYLE = {
  version: 8 as const,
  sources: {
    osm: {
      type: "raster" as const,
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "\u00a9 OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
};
