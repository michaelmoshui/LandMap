import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { fetchBoundary, fetchLayerFeatures } from "../api/client";
import type { LayerMeta } from "../api/types";
import { BASE_MAP_STYLE } from "../map/baseMapStyle";
import { buildMapLayers, sourceIdFor } from "../map/buildLayers";
import { DEFAULT_ZOOM, VANCOUVER_CENTER } from "../map/layerStyles";
import {
  buildSelectionLayers,
  type SelectedBoundary,
  selectionSourceId,
} from "../map/selection";

interface MapViewProps {
  layers: LayerMeta[];
  active: Set<string>;
  selections: SelectedBoundary[];
}

export default function MapView({ layers, active, selections }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const loadedRef = useRef(false);
  // Boundary ids currently rendered as selection highlights on the map.
  const renderedSelectionsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASE_MAP_STYLE,
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
      renderedSelectionsRef.current = new Set();
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

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const sync = async () => {
      const rendered = renderedSelectionsRef.current;
      const desired = new Set(selections.map((s) => s.id));

      for (const boundaryId of [...rendered]) {
        if (desired.has(boundaryId)) continue;
        for (const spec of buildSelectionLayers(boundaryId, "")) {
          if (map.getLayer(spec.id)) map.removeLayer(spec.id);
        }
        const sourceId = selectionSourceId(boundaryId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
        rendered.delete(boundaryId);
      }

      for (const selection of selections) {
        if (rendered.has(selection.id)) continue;
        const sourceId = selectionSourceId(selection.id);
        if (!map.getSource(sourceId)) {
          try {
            const feature = await fetchBoundary(selection.id);
            if (!map.getSource(sourceId)) {
              map.addSource(sourceId, { type: "geojson", data: feature as never });
            }
          } catch {
            continue;
          }
        }
        for (const spec of buildSelectionLayers(selection.id, selection.color)) {
          if (!map.getLayer(spec.id)) map.addLayer(spec as never);
        }
        rendered.add(selection.id);
      }
    };

    if (loadedRef.current) {
      void sync();
    } else {
      map.once("load", () => void sync());
    }
  }, [selections]);

  return <div className="map" ref={containerRef} data-testid="map" />;
}
