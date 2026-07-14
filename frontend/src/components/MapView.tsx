import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { fetchLayerFeatures } from "../api/client";
import type { LayerMeta, RegionMeta } from "../api/types";
import { buildMapLayers, sourceIdFor } from "../map/buildLayers";
import { DEFAULT_ZOOM, OSM_STYLE, VANCOUVER_CENTER } from "../map/layerStyles";
import { popupHtml } from "../map/popup";

interface MapViewProps {
  layers: LayerMeta[];
  active: Set<string>;
  region?: RegionMeta | null;
}

export default function MapView({ layers, active, region }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const loadedRef = useRef(false);
  // Style-layer ids we have added, so switching regions can remove stale ones.
  const addedRef = useRef<Set<string>>(new Set());

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
    // One shared click handler: show the top feature of any active layer.
    map.on("click", (e) => {
      const layerIds = [...addedRef.current].filter((id) => map.getLayer(id));
      if (layerIds.length === 0) return;
      const features = map.queryRenderedFeatures(e.point, { layers: layerIds });
      const properties = features[0]?.properties;
      if (!properties) return;
      new maplibregl.Popup({ maxWidth: "320px" })
        .setLngLat(e.lngLat)
        .setHTML(popupHtml(properties))
        .addTo(map);
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      loadedRef.current = false;
      addedRef.current = new Set();
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !region) return;
    map.flyTo({ center: region.center, zoom: region.zoom });
  }, [region?.id]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const sync = async () => {
      const desired = new Set<string>();
      for (const layer of layers) {
        if (!active.has(layer.id)) continue;
        for (const spec of buildMapLayers(layer.id, layer.category)) {
          desired.add(spec.id);
        }
      }

      // Remove layers that are toggled off or belong to another region.
      for (const id of [...addedRef.current]) {
        if (!desired.has(id)) {
          if (map.getLayer(id)) map.removeLayer(id);
          addedRef.current.delete(id);
        }
      }

      for (const layer of layers) {
        if (!active.has(layer.id)) continue;
        const sourceId = sourceIdFor(layer.id);
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
        for (const spec of buildMapLayers(layer.id, layer.category)) {
          if (!map.getLayer(spec.id)) {
            map.addLayer(spec as never);
          }
          addedRef.current.add(spec.id);
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
