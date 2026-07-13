import type { BoundaryKind, FeatureCollection, GeoFeature } from "../api/types";
import { sourceIdFor } from "./buildLayers";

// Pure helpers for the clickable boundary layers (municipalities and
// neighborhoods). Selected boundaries keep the normal map colors; once at
// least one is selected, everything else is dimmed by a single inverse mask
// (world minus the selected shapes). Dimming per non-selected feature instead
// would make the visual state depend on the dataset: coverage gaps would stay
// bright as if selected, and overlapping features would double-darken
// (see BUG_LOG.md BUG-008). Lots are excluded: they use the colored highlight
// in selection.ts instead.

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

export function maskSourceIdFor(layerId: string): string {
  return `${sourceIdFor(layerId)}-mask`;
}

type Ring = number[][];

// Covers the whole map; selected shapes are cut out of it as holes.
const WORLD_RING: Ring = [
  [-180, -85],
  [180, -85],
  [180, 85],
  [-180, 85],
  [-180, -85],
];

function polygonsOf(feature: GeoFeature): Ring[][] {
  if (feature.geometry.type === "Polygon") {
    return [feature.geometry.coordinates as Ring[]];
  }
  if (feature.geometry.type === "MultiPolygon") {
    return feature.geometry.coordinates as Ring[][];
  }
  return [];
}

/**
 * Build the dim mask for one boundary layer: nothing when no selection (the
 * darkening only takes effect after the first selection), otherwise the world
 * with every selected shape cut out. Interior rings (holes) of selected shapes
 * are not part of the selection, so they are dimmed again as their own parts.
 */
export function buildDimMask(selectedFeatures: GeoFeature[]): FeatureCollection {
  if (selectedFeatures.length === 0) {
    return { type: "FeatureCollection", features: [] };
  }
  const cutouts: Ring[] = [];
  const redimmedHoles: Ring[][] = [];
  for (const feature of selectedFeatures) {
    for (const rings of polygonsOf(feature)) {
      const [exterior, ...holes] = rings;
      if (!exterior) continue;
      cutouts.push(exterior);
      redimmedHoles.push(...holes.map((hole) => [hole]));
    }
  }
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "MultiPolygon",
          coordinates: [[WORLD_RING, ...cutouts], ...redimmedHoles],
        },
        properties: {},
      },
    ],
  };
}

export interface BoundaryLayerSpec {
  id: string;
  type: "fill" | "line";
  source: string;
  paint: Record<string, unknown>;
}

/**
 * Build the MapLibre layers for one boundary map layer: an invisible fill for
 * cursor hit-testing, the dim mask overlay, and the boundary outlines.
 */
export function buildBoundaryLayers(layerId: string): BoundaryLayerSpec[] {
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
      source: maskSourceIdFor(layerId),
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
