import type {
  BoundarySummary,
  DataSource,
  FeatureCollection,
  GeoFeature,
  LayerMeta,
  RegionMeta,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function getJson<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) {
    throw new Error(`Request failed: ${resp.status} ${path}`);
  }
  return (await resp.json()) as T;
}

function regionQuery(region?: string): string {
  return region ? `?region=${encodeURIComponent(region)}` : "";
}

export function fetchLayers(region?: string): Promise<LayerMeta[]> {
  return getJson<LayerMeta[]>(`/layers${regionQuery(region)}`);
}

export function fetchLayerFeatures(layerId: string): Promise<FeatureCollection> {
  return getJson<FeatureCollection>(`/layers/${layerId}/features`);
}

export function fetchRegions(): Promise<RegionMeta[]> {
  return getJson<RegionMeta[]>("/regions");
}

export function fetchSources(region?: string): Promise<DataSource[]> {
  return getJson<DataSource[]>(`/sources${regionQuery(region)}`);
}

export function searchBoundaries(query: string): Promise<BoundarySummary[]> {
  return getJson<BoundarySummary[]>(`/boundaries/search?q=${encodeURIComponent(query)}`);
}

export function fetchBoundary(boundaryId: string): Promise<GeoFeature> {
  return getJson<GeoFeature>(`/boundaries/${boundaryId}`);
}
