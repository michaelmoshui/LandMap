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
