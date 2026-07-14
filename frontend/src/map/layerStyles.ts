import type { LayerCategory } from "../api/types";

// Color used to render each layer's features on the map.
export const CATEGORY_COLORS: Record<LayerCategory, string> = {
  baseline: "#2563eb",
  planned: "#dc2626",
};

export function colorForCategory(category: LayerCategory): string {
  return CATEGORY_COLORS[category];
}

/**
 * Per-layer rendering tweaks. Features may also carry their own `color`
 * property (e.g. TransLink's official route colours baked in by ingestion),
 * which always wins over the layer/category color.
 */
export interface LayerStyle {
  /** Fallback color for features without a `color` property. */
  color?: string;
  lineWidth?: number;
  lineOpacity?: number;
  /** Circle radius: a number or a MapLibre zoom expression. */
  circleRadius?: number | unknown[];
  circleStrokeWidth?: number;
  /** Metro-map station look: white core with a feature-colored ring. */
  hollowPoints?: boolean;
}

export const LAYER_STYLES: Record<string, LayerStyle> = {
  "skytrain-lines": { lineWidth: 4.5 },
  "skytrain-stations": { hollowPoints: true, circleRadius: 5, circleStrokeWidth: 2.5 },
  "seabus-wce": { lineWidth: 3, hollowPoints: true, circleRadius: 4.5, circleStrokeWidth: 2.5 },
  "bus-routes": { lineWidth: 1.8, lineOpacity: 0.85 },
  "bus-stops": {
    // TransLink's system-map gray-blue; dots grow as street detail appears.
    color: "#7A99AC",
    circleRadius: ["interpolate", ["linear"], ["zoom"], 10, 1.2, 13, 3, 16, 5],
    circleStrokeWidth: 0.8,
  },
};

export function styleForLayer(layerId: string): LayerStyle {
  return LAYER_STYLES[layerId] ?? {};
}

// The Greater Vancouver Area viewport.
export const VANCOUVER_CENTER: [number, number] = [-123.02, 49.24];
export const DEFAULT_ZOOM = 10.5;
