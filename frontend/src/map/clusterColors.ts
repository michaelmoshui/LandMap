import type { FeatureCollection, GeoFeature } from "../api/types";

// Colour road-construction (and similar) features so that clusters sitting
// close together are told apart at a glance. Features are grouped into
// clusters, clusters that are near each other are treated as "adjacent", and a
// small palette is graph-coloured so no two adjacent clusters share a colour.
// Far-apart clusters may reuse a colour - that is fine and keeps the palette
// small. Pure and unit-testable; MapView bakes the result into the source and
// buildLayers' `coalesce(get color, ...)` then renders it.

// Ten visually distinct hues. Kept deliberately small (see module doc).
export const CLUSTER_COLORS: readonly string[] = [
  "#e6194b", // red
  "#3cb44b", // green
  "#4363d8", // blue
  "#f58231", // orange
  "#911eb4", // purple
  "#008080", // teal
  "#f032e6", // magenta
  "#9a6324", // brown
  "#808000", // olive
  "#42d4f4", // cyan
];

// Layers whose features should be cluster-coloured instead of the flat
// category colour.
const CLUSTERED_LAYER_IDS = new Set(["road-construction", "gta-road-construction"]);

export function isClusteredLayer(layerId: string): boolean {
  return CLUSTERED_LAYER_IDS.has(layerId);
}

// Two clusters closer than this (great-circle, between their centroids) are
// considered neighbours and must not share a colour.
export const CLUSTER_ADJACENCY_KM = 2;

type Position = [number, number];

/** Recursively collect every [lng, lat] position out of a GeoJSON coordinate array. */
function collectPositions(coords: unknown, out: Position[]): void {
  if (!Array.isArray(coords)) return;
  if (typeof coords[0] === "number" && typeof coords[1] === "number") {
    out.push([coords[0], coords[1]]);
    return;
  }
  for (const child of coords) collectPositions(child, out);
}

/** Mean of a feature's positions, or null if it has no coordinates. */
export function featureCentroid(feature: GeoFeature): Position | null {
  const positions: Position[] = [];
  collectPositions(feature.geometry?.coordinates, positions);
  if (positions.length === 0) return null;
  let lng = 0;
  let lat = 0;
  for (const [x, y] of positions) {
    lng += x;
    lat += y;
  }
  return [lng / positions.length, lat / positions.length];
}

const EARTH_RADIUS_KM = 6371;

/** Great-circle distance between two [lng, lat] points, in kilometres. */
export function haversineKm(a: Position, b: Position): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(b[1] - a[1]);
  const dLng = toRad(a[0] - b[0]) * -1;
  const lat1 = toRad(a[1]);
  const lat2 = toRad(b[1]);
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}

interface Cluster {
  key: string;
  centroid: Position;
  featureIndices: number[];
  neighbours: Set<number>; // indices into the clusters array
}

/**
 * Key that identifies the project a feature belongs to. Prefer the (unique)
 * source url; fall back to the project name, then to a per-feature id so a
 * feature always forms at least its own cluster.
 */
function clusterKey(feature: GeoFeature, index: number): string {
  const props = feature.properties ?? {};
  const url = props.url;
  if (typeof url === "string" && url) return `url:${url}`;
  const project = props.project;
  if (typeof project === "string" && project) return `project:${project}`;
  return `idx:${index}`;
}

/**
 * Greedy graph colouring: process the most-connected clusters first and give
 * each the lowest-indexed palette colour none of its already-coloured
 * neighbours use. If every colour is taken by a neighbour (more neighbours than
 * colours), fall back to the colour the fewest neighbours use.
 */
function colourClusters(clusters: Cluster[], palette: readonly string[]): string[] {
  const order = clusters
    .map((_, i) => i)
    .sort((a, b) => {
      const byDegree = clusters[b].neighbours.size - clusters[a].neighbours.size;
      return byDegree !== 0 ? byDegree : clusters[a].key.localeCompare(clusters[b].key);
    });

  const colourOf: (number | null)[] = clusters.map(() => null);
  for (const i of order) {
    const used = new Set<number>();
    for (const n of clusters[i].neighbours) {
      const c = colourOf[n];
      if (c !== null) used.add(c);
    }
    let chosen = palette.findIndex((_, ci) => !used.has(ci));
    if (chosen === -1) {
      // Palette exhausted by neighbours: pick the least-conflicting colour.
      const counts = palette.map(() => 0);
      for (const n of clusters[i].neighbours) {
        const c = colourOf[n];
        if (c !== null) counts[c] += 1;
      }
      chosen = counts.indexOf(Math.min(...counts));
    }
    colourOf[i] = chosen;
  }
  return colourOf.map((c) => palette[c ?? 0]);
}

/**
 * Return a copy of the collection with a `color` baked into every feature so
 * that nearby clusters render in different colours. Features that already carry
 * a `color` are left untouched.
 */
export function assignClusterColors(
  collection: FeatureCollection,
  adjacencyKm: number = CLUSTER_ADJACENCY_KM,
  palette: readonly string[] = CLUSTER_COLORS,
): FeatureCollection {
  // Group features into clusters by project key, accumulating their centroids.
  const byKey = new Map<string, Cluster>();
  const clusters: Cluster[] = [];
  collection.features.forEach((feature, index) => {
    const centroid = featureCentroid(feature);
    if (!centroid) return;
    const key = clusterKey(feature, index);
    let cluster = byKey.get(key);
    if (!cluster) {
      cluster = { key, centroid: [0, 0], featureIndices: [], neighbours: new Set() };
      byKey.set(key, cluster);
      clusters.push(cluster);
    }
    cluster.featureIndices.push(index);
  });

  // Centroid of a cluster = mean of its member features' centroids.
  for (const cluster of clusters) {
    let lng = 0;
    let lat = 0;
    for (const i of cluster.featureIndices) {
      const c = featureCentroid(collection.features[i]);
      if (c) {
        lng += c[0];
        lat += c[1];
      }
    }
    const n = cluster.featureIndices.length;
    cluster.centroid = [lng / n, lat / n];
  }

  // Build adjacency between clusters whose centroids are within the threshold.
  for (let i = 0; i < clusters.length; i += 1) {
    for (let j = i + 1; j < clusters.length; j += 1) {
      if (haversineKm(clusters[i].centroid, clusters[j].centroid) <= adjacencyKm) {
        clusters[i].neighbours.add(j);
        clusters[j].neighbours.add(i);
      }
    }
  }

  const clusterColour = colourClusters(clusters, palette);
  const colourByFeatureIndex = new Map<number, string>();
  clusters.forEach((cluster, ci) => {
    for (const i of cluster.featureIndices) colourByFeatureIndex.set(i, clusterColour[ci]);
  });

  return {
    ...collection,
    features: collection.features.map((feature, index) => {
      if (feature.properties?.color) return feature;
      const color = colourByFeatureIndex.get(index);
      if (!color) return feature;
      return { ...feature, properties: { ...feature.properties, color } };
    }),
  };
}
