import type { FeatureCollection, LayerMeta } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function getJson<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) {
    throw new Error(`Request failed: ${resp.status} ${path}`);
  }
  return (await resp.json()) as T;
}

export function fetchLayers(): Promise<LayerMeta[]> {
  return getJson<LayerMeta[]>("/layers");
}

export function fetchLayerFeatures(layerId: string): Promise<FeatureCollection> {
  return getJson<FeatureCollection>(`/layers/${layerId}/features`);
}
