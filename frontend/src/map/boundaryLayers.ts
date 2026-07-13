import type { BoundaryKind } from "../api/types";
import { sourceIdFor } from "./buildLayers";

// Pure helpers for the clickable boundary layers (municipalities and
// neighborhoods). Selected boundaries keep the normal map colors; once at
// least one is selected, every non-selected boundary of that kind is dimmed.
// Lots are excluded: they use the colored highlight in selection.ts instead.

export const BOUNDARY_LAYER_BY_KIND: Partial<Record<BoundaryKind, string>> = {
  municipality: "municipality-boundaries",
  neighborhood: "neighborhood-boundaries",
};

const KIND_BY_BOUNDARY_LAYER = new Map<string, BoundaryKind>(
  Object.entries(BOUNDARY_LAYER_BY_KIND).map(([kind, layerId]) => [
    layerId,
    kind as BoundaryKind,
  ]),
);

export function isBoundaryLayer(layerId: string): boolean {
  return KIND_BY_BOUNDARY_LAYER.has(layerId);
}

export function kindForBoundaryLayer(layerId: string): BoundaryKind | undefined {
  return KIND_BY_BOUNDARY_LAYER.get(layerId);
}

export function hitLayerIdFor(layerId: string): string {
  return `${layerId}-hit`;
}

export function dimLayerIdFor(layerId: string): string {
  return `${layerId}-dim`;
}

/**
 * Filter for the dim layer: with no selection nothing is dimmed; with at least
 * one selection every non-selected boundary is dimmed.
 */
export function dimFilter(selectedIds: string[]): unknown[] {
  if (selectedIds.length === 0) {
    return ["==", ["get", "id"], "__none-selected__"];
  }
  return ["!", ["in", ["get", "id"], ["literal", selectedIds]]];
}

export interface BoundaryLayerSpec {
  id: string;
  type: "fill" | "line";
  source: string;
  filter?: unknown[];
  paint: Record<string, unknown>;
}

/**
 * Build the MapLibre layers for one boundary map layer: an invisible fill for
 * cursor hit-testing, the dim overlay for non-selected boundaries, and the
 * boundary outlines.
 */
export function buildBoundaryLayers(layerId: string, selectedIds: string[]): BoundaryLayerSpec[] {
  const source = sourceIdFor(layerId);
  return [
    {
      id: hitLayerIdFor(layerId),
      type: "fill",
      source,
      paint: { "fill-color": "#000000", "fill-opacity": 0 },
    },
    {
      id: dimLayerIdFor(layerId),
      type: "fill",
      source,
      filter: dimFilter(selectedIds),
      paint: { "fill-color": "#475569", "fill-opacity": 0.45 },
    },
    {
      id: `${layerId}-outline`,
      type: "line",
      source,
      paint: { "line-color": "#64748b", "line-width": 1.5 },
    },
  ];
}
