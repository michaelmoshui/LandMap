// Mirrors backend/app/schemas/layers.py. Keep in sync (see AGENTS.md).

export type LayerCategory = "baseline" | "planned";

export interface LayerMeta {
  id: string;
  title: string;
  description: string;
  category: LayerCategory;
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
