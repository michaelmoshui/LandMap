import type { BoundarySummary } from "../api/types";

// Pure helpers for highlighting selected boundaries (municipalities,
// neighborhoods, lots). Kept separate from the React/MapLibre glue so they are
// unit-testable.

// A boundary the user has selected, with the highlight color assigned to it.
export interface SelectedBoundary extends BoundarySummary {
  color: string;
}

// Distinct, high-contrast highlight colors. Each new selection takes the first
// color not already in use, so removing a selection frees its color.
export const SELECTION_COLORS = [
  "#e6194b", // red
  "#3cb44b", // green
  "#4363d8", // blue
  "#f58231", // orange
  "#911eb4", // purple
  "#0ea5b7", // teal
  "#f032e6", // magenta
  "#9a6324", // brown
] as const;

export function nextSelectionColor(inUse: string[]): string {
  const free = SELECTION_COLORS.find((color) => !inUse.includes(color));
  return free ?? SELECTION_COLORS[inUse.length % SELECTION_COLORS.length];
}

export function selectionSourceId(boundaryId: string): string {
  return `landmap-selection-src-${boundaryId}`;
}

export interface SelectionLayerSpec {
  id: string;
  type: "fill" | "line";
  source: string;
  paint: Record<string, unknown>;
}

/**
 * Build the MapLibre layers that highlight one selected boundary: a translucent
 * fill plus a solid outline, both in the selection's color.
 */
export function buildSelectionLayers(boundaryId: string, color: string): SelectionLayerSpec[] {
  const source = selectionSourceId(boundaryId);
  return [
    {
      id: `selection-${boundaryId}-fill`,
      type: "fill",
      source,
      paint: { "fill-color": color, "fill-opacity": 0.3 },
    },
    {
      id: `selection-${boundaryId}-outline`,
      type: "line",
      source,
      paint: { "line-color": color, "line-width": 2.5 },
    },
  ];
}
