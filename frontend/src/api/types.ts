// Mirrors backend/app/schemas/layers.py. Keep in sync (see AGENTS.md).

export type LayerCategory = "baseline" | "planned";

export interface LayerMeta {
  id: string;
  title: string;
  description: string;
  category: LayerCategory;
  region: string;
}

export interface RegionMeta {
  id: string;
  title: string;
  center: [number, number]; // [lng, lat]
  zoom: number;
}

export interface DataSource {
  id: string;
  name: string;
  description: string;
  url: string;
  region: string;
  group: string;
}

export interface GeoFeature {
  type: "Feature";
  geometry: {
    type: string;
    coordinates: unknown;
  };
  properties: Record<string, unknown>;
}

export interface FeatureCollection {
  type: "FeatureCollection";
  features: GeoFeature[];
}
