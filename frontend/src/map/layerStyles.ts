import type { FeatureCollection, LayerCategory } from "../api/types";

// Color used to render each layer's features on the map.
export const CATEGORY_COLORS: Record<LayerCategory, string> = {
  baseline: "#2563eb",
  planned: "#dc2626",
};

export function colorForCategory(category: LayerCategory): string {
  return CATEGORY_COLORS[category];
}

// Layers whose features are municipalities/cities. They get a rotating palette
// (see assignCityColors) so neighbouring cities are told apart at a glance,
// instead of every polygon sharing one flat category colour.
const CITY_INFO_LAYER_IDS = new Set(["demographics", "gta-demographics"]);

export function isCityInfoLayer(layerId: string): boolean {
  return CITY_INFO_LAYER_IDS.has(layerId);
}

// Six distinct hues. Adjacent cities are guaranteed different colours (see
// assignCityColors); six gives the greedy colourer plenty of headroom so the
// result also stays visually varied, not just technically valid.
export const CITY_COLORS: readonly string[] = [
  "#2563eb", // blue
  "#16a34a", // green
  "#d97706", // amber
  "#9333ea", // purple
  "#0891b2", // cyan
  "#db2777", // pink
];

// Snap vertices to a grid (~11 m) before comparing so that a shared border maps
// to the same key on both sides. This matches the census layer's coordinate
// precision and tolerates minor per-polygon simplification differences; the
// worst case is two near-but-not-touching cities being treated as neighbours,
// which only costs an extra colour.
const VERTEX_DECIMALS = 4;

function vertexKey(lng: number, lat: number): string {
  return `${lng.toFixed(VERTEX_DECIMALS)},${lat.toFixed(VERTEX_DECIMALS)}`;
}

// Walk a Polygon/MultiPolygon coordinate tree and collect every vertex key.
function vertexKeysOf(feature: FeatureCollection["features"][number]): string[] {
  const keys: string[] = [];
  const walk = (node: unknown): void => {
    if (!Array.isArray(node)) return;
    if (typeof node[0] === "number" && typeof node[1] === "number") {
      keys.push(vertexKey(node[0], node[1]));
      return;
    }
    for (const child of node) walk(child);
  };
  walk(feature.geometry?.coordinates);
  return keys;
}

/**
 * Return a copy of the collection with a `color` baked into each feature so
 * that no two adjacent cities share a hue. Adjacency is detected from shared
 * boundary vertices (neighbouring polygons share exact coordinates), then a
 * greedy graph colouring assigns each feature the first palette colour not
 * used by an already-coloured neighbour. Features that already carry a `color`
 * keep it (a feature's own colour always wins, matching buildMapLayers'
 * coalesce) and still constrain their neighbours.
 */
export function assignCityColors(collection: FeatureCollection): FeatureCollection {
  const features = collection.features;

  // Map each shared vertex to the features touching it, then derive neighbours.
  const featuresByVertex = new Map<string, number[]>();
  features.forEach((feature, index) => {
    for (const key of new Set(vertexKeysOf(feature))) {
      const bucket = featuresByVertex.get(key);
      if (bucket) bucket.push(index);
      else featuresByVertex.set(key, [index]);
    }
  });
  const neighbors: Set<number>[] = features.map(() => new Set<number>());
  for (const bucket of featuresByVertex.values()) {
    for (const a of bucket) {
      for (const b of bucket) {
        if (a !== b) neighbors[a].add(b);
      }
    }
  }

  const assigned: (string | undefined)[] = features.map(
    (feature) => (feature.properties?.color as string | undefined) ?? undefined,
  );
  features.forEach((_, index) => {
    if (assigned[index] !== undefined) return; // keeps its own colour
    const taken = new Set<string>();
    for (const other of neighbors[index]) {
      if (assigned[other] !== undefined) taken.add(assigned[other] as string);
    }
    assigned[index] =
      CITY_COLORS.find((color) => !taken.has(color)) ?? CITY_COLORS[index % CITY_COLORS.length];
  });

  return {
    ...collection,
    features: features.map((feature, index) =>
      feature.properties?.color
        ? feature
        : { ...feature, properties: { ...feature.properties, color: assigned[index] } },
    ),
  };
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

// Shared looks for the transit layers in both regions.
const RAIL_LINES: LayerStyle = { lineWidth: 4.5 };
const STATIONS: LayerStyle = { hollowPoints: true, circleRadius: 5, circleStrokeWidth: 2.5 };
const REGIONAL_RAIL: LayerStyle = {
  lineWidth: 3,
  hollowPoints: true,
  circleRadius: 4.5,
  circleStrokeWidth: 2.5,
};
const BUS_ROUTES: LayerStyle = { lineWidth: 1.8, lineOpacity: 0.85 };
const BUS_STOPS: LayerStyle = {
  // Neutral map gray-blue for stop dots; they grow as street detail appears.
  color: "#7A99AC",
  circleRadius: ["interpolate", ["linear"], ["zoom"], 10, 1.2, 13, 3, 16, 5],
  circleStrokeWidth: 0.8,
};

export const LAYER_STYLES: Record<string, LayerStyle> = {
  // Greater Vancouver Area (TransLink)
  "skytrain-lines": RAIL_LINES,
  "skytrain-stations": STATIONS,
  "seabus-wce": REGIONAL_RAIL,
  "bus-routes": BUS_ROUTES,
  "bus-stops": BUS_STOPS,
  // Greater Toronto Area (TTC + GO Transit)
  "gta-subway-lines": RAIL_LINES,
  "gta-subway-stations": STATIONS,
  "gta-streetcar-lines": { lineWidth: 2.2 },
  "gta-bus-routes": BUS_ROUTES,
  "gta-bus-stops": BUS_STOPS,
  "gta-go-transit": REGIONAL_RAIL,
};

export function styleForLayer(layerId: string): LayerStyle {
  return LAYER_STYLES[layerId] ?? {};
}

// The Greater Vancouver Area viewport.
export const VANCOUVER_CENTER: [number, number] = [-123.02, 49.24];
export const DEFAULT_ZOOM = 10.5;
