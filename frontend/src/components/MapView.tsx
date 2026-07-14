import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { fetchBoundary, fetchLayerFeatures } from "../api/client";
import type { BoundarySummary, FeatureCollection, LayerMeta, RegionMeta } from "../api/types";
import { BASE_MAP_STYLE } from "../map/baseMapStyle";
import {
  BOUNDARY_LAYER_IDS,
  buildBoundaryLayers,
  buildDimMask,
  hitLayerIdFor,
  isBoundaryLayer,
  kindForBoundaryLayer,
  maskSourceIdFor,
} from "../map/boundaryLayers";
import { buildMapLayers, sourceIdFor } from "../map/buildLayers";
import { DEFAULT_ZOOM, VANCOUVER_CENTER } from "../map/layerStyles";
import { popupHtml } from "../map/popup";
import {
  buildSelectionLayers,
  type SelectedBoundary,
  selectionSourceId,
} from "../map/selection";

interface MapViewProps {
  layers: LayerMeta[];
  active: Set<string>;
  region?: RegionMeta | null;
  selections: SelectedBoundary[];
  onBoundaryToggle: (boundary: BoundarySummary) => void;
}

const HIT_LAYER_IDS = BOUNDARY_LAYER_IDS.map(hitLayerIdFor);

// Style-layer ids owned by the boundary layers, so the data-layer popup
// handler can ignore them (boundaries are selected, not popped up).
const BOUNDARY_SPEC_IDS = new Set(
  BOUNDARY_LAYER_IDS.flatMap((id) => buildBoundaryLayers(id).map((spec) => spec.id)),
);

function selectedFeaturesFor(
  layerId: string,
  selections: SelectedBoundary[],
  data: FeatureCollection | undefined,
): FeatureCollection["features"] {
  const kind = kindForBoundaryLayer(layerId);
  const selectedIds = new Set(
    selections.filter((s) => s.kind === kind).map((s) => s.id),
  );
  if (selectedIds.size === 0 || !data) return [];
  return data.features.filter((f) => selectedIds.has((f.properties.id as string) ?? ""));
}

export default function MapView({
  layers,
  active,
  region,
  selections,
  onBoundaryToggle,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const loadedRef = useRef(false);
  // Style-layer ids we have added, so switching regions can remove stale ones.
  const addedRef = useRef<Set<string>>(new Set());
  // Lot ids currently rendered as colored highlights on the map.
  const renderedLotsRef = useRef<Set<string>>(new Set());
  // Fetched FeatureCollections per layer, used to build the dim masks.
  const layerDataRef = useRef<Map<string, FeatureCollection>>(new Map());
  const onBoundaryToggleRef = useRef(onBoundaryToggle);
  onBoundaryToggleRef.current = onBoundaryToggle;

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
    // Popup handler: show the top feature of any active data layer. Boundary
    // layers are excluded - they are selected (see the handler below), not
    // popped up.
    map.on("click", (e) => {
      const layerIds = [...addedRef.current].filter(
        (id) => map.getLayer(id) && !BOUNDARY_SPEC_IDS.has(id),
      );
      if (layerIds.length === 0) return;
      const features = map.queryRenderedFeatures(e.point, { layers: layerIds });
      const properties = features[0]?.properties;
      if (!properties) return;
      new maplibregl.Popup({ maxWidth: "320px" })
        .setLngLat(e.lngLat)
        .setHTML(popupHtml(properties))
        .addTo(map);
    });

    // Cursor selection of boundaries. One global click handler so overlapping
    // boundary layers toggle only the topmost feature under the cursor.
    map.on("click", (event) => {
      const present = HIT_LAYER_IDS.filter((id) => map.getLayer(id));
      if (present.length === 0) return;
      const hit = map.queryRenderedFeatures(event.point, { layers: present })[0];
      const props = hit?.properties as Partial<BoundarySummary> | undefined;
      if (props?.id && props.name && props.kind) {
        onBoundaryToggleRef.current({ id: props.id, name: props.name, kind: props.kind });
      }
    });
    for (const hitId of HIT_LAYER_IDS) {
      map.on("mouseenter", hitId, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", hitId, () => {
        map.getCanvas().style.cursor = "";
      });
    }

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      loadedRef.current = false;
      addedRef.current = new Set();
      renderedLotsRef.current = new Set();
      layerDataRef.current = new Map();
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
        const specs = isBoundaryLayer(layer.id)
          ? buildBoundaryLayers(layer.id)
          : buildMapLayers(layer.id, layer.category);
        for (const spec of specs) {
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
        const specs = isBoundaryLayer(layer.id)
          ? buildBoundaryLayers(layer.id)
          : buildMapLayers(layer.id, layer.category);
        if (!map.getSource(sourceId)) {
          try {
            const data = await fetchLayerFeatures(layer.id);
            layerDataRef.current.set(layer.id, data);
            if (!map.getSource(sourceId)) {
              map.addSource(sourceId, { type: "geojson", data: data as never });
            }
          } catch {
            continue;
          }
        }

        if (isBoundaryLayer(layer.id)) {
          // Dim everything except the selected shapes, so the map always
          // matches the selection list regardless of dataset coverage.
          const mask = buildDimMask(
            selectedFeaturesFor(layer.id, selections, layerDataRef.current.get(layer.id)),
          );
          const maskId = maskSourceIdFor(layer.id);
          const maskSource = map.getSource(maskId) as maplibregl.GeoJSONSource | undefined;
          if (maskSource) maskSource.setData(mask as never);
          else map.addSource(maskId, { type: "geojson", data: mask as never });
        }

        for (const spec of specs) {
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
  }, [layers, active, selections]);

  // Lots are too small for the dim treatment; they keep a colored highlight.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const lots = selections.filter((s) => s.kind === "lot");

    const sync = async () => {
      const rendered = renderedLotsRef.current;
      const desired = new Set(lots.map((s) => s.id));

      for (const boundaryId of [...rendered]) {
        if (desired.has(boundaryId)) continue;
        for (const spec of buildSelectionLayers(boundaryId, "")) {
          if (map.getLayer(spec.id)) map.removeLayer(spec.id);
        }
        const sourceId = selectionSourceId(boundaryId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
        rendered.delete(boundaryId);
      }

      for (const selection of lots) {
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
