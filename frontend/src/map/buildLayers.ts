import type { LayerCategory } from "../api/types";
import { colorForCategory } from "./layerStyles";

// Pure helpers for translating a LandMap layer into MapLibre style layers.
// Kept separate from the React/MapLibre glue so they are unit-testable.

export function sourceIdFor(layerId: string): string {
  return `landmap-src-${layerId}`;
}

export interface MapLayerSpec {
  id: string;
  type: "circle" | "line" | "fill";
  source: string;
  filter: unknown[];
  paint: Record<string, unknown>;
}

// MapLibre's geometry-type expression can report Multi* variants, so every
// filter matches both the singular and Multi form.
function geometryFilter(...types: string[]): unknown[] {
  return ["in", ["geometry-type"], ["literal", types]];
}

/**
 * Build the MapLibre layer specs needed to render a LandMap layer. Polygons
 * render as translucent fills, lines as strokes, points as circles; all
 * colored by category. Fills come first so points/lines stack above them.
 */
export function buildMapLayers(layerId: string, category: LayerCategory): MapLayerSpec[] {
  const source = sourceIdFor(layerId);
  const color = colorForCategory(category);
  return [
    {
      id: `${layerId}-fills`,
      type: "fill",
      source,
      filter: geometryFilter("Polygon", "MultiPolygon"),
      paint: {
        "fill-color": color,
        "fill-opacity": 0.18,
        "fill-outline-color": color,
      },
    },
    {
      id: `${layerId}-lines`,
      type: "line",
      source,
      filter: geometryFilter("LineString", "MultiLineString"),
      paint: {
        "line-color": color,
        "line-width": 4,
      },
    },
    {
      id: `${layerId}-points`,
      type: "circle",
      source,
      filter: geometryFilter("Point", "MultiPoint"),
      paint: {
        "circle-radius": 6,
        "circle-color": color,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    },
  ];
}
