import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { fetchLayerFeatures } from "../api/client";
import type { LayerMeta } from "../api/types";
import { buildMapLayers, sourceIdFor } from "../map/buildLayers";
import { DEFAULT_ZOOM, OSM_STYLE, VANCOUVER_CENTER } from "../map/layerStyles";

interface MapViewProps {
  layers: LayerMeta[];
  active: Set<string>;
}

export default function MapView({ layers, active }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const loadedRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center: VANCOUVER_CENTER,
      zoom: DEFAULT_ZOOM,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.on("load", () => {
      loadedRef.current = true;
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      loadedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const sync = async () => {
      for (const layer of layers) {
        const sourceId = sourceIdFor(layer.id);
        const specs = buildMapLayers(layer.id, layer.category);
        const shouldShow = active.has(layer.id);

        if (shouldShow) {
          if (!map.getSource(sourceId)) {
            try {
              const data = await fetchLayerFeatures(layer.id);
              if (!map.getSource(sourceId)) {
                map.addSource(sourceId, { type: "geojson", data: data as never });
              }
            } catch {
              continue;
            }
          }
          for (const spec of specs) {
            if (!map.getLayer(spec.id)) {
              map.addLayer(spec as never);
            }
          }
        } else {
          for (const spec of specs) {
            if (map.getLayer(spec.id)) map.removeLayer(spec.id);
          }
        }
      }
    };

    if (loadedRef.current) {
      void sync();
    } else {
      map.once("load", () => void sync());
    }
  }, [layers, active]);

  return <div className="map" ref={containerRef} data-testid="map" />;
}
