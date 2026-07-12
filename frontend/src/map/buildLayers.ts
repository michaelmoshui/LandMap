import type { LayerCategory } from "../api/types";
import { colorForCategory } from "./layerStyles";

// Pure helpers for translating a LandMap layer into MapLibre style layers.
// Kept separate from the React/MapLibre glue so they are unit-testable.

export function sourceIdFor(layerId: string): string {
  return `landmap-src-${layerId}`;
}

export interface MapLayerSpec {
  id: string;
  type: "circle" | "line";
  source: string;
  filter: unknown[];
  paint: Record<string, unknown>;
}

/**
 * Build the MapLibre layer specs needed to render a LandMap layer. Points render
 * as circles, lines as strokes; both colored by category.
 */
export function buildMapLayers(layerId: string, category: LayerCategory): MapLayerSpec[] {
  const source = sourceIdFor(layerId);
  const color = colorForCategory(category);
  return [
    {
      id: `${layerId}-points`,
      type: "circle",
      source,
      filter: ["==", ["geometry-type"], "Point"],
      paint: {
        "circle-radius": 6,
        "circle-color": color,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    },
    {
      id: `${layerId}-lines`,
      type: "line",
      source,
      filter: ["==", ["geometry-type"], "LineString"],
      paint: {
        "line-color": color,
        "line-width": 4,
      },
    },
  ];
}
