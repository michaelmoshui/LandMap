import { useEffect, useState } from "react";

import { fetchLayers, fetchRegions, fetchSources } from "./api/client";
import type { BoundarySummary, DataSource, LayerMeta, RegionMeta } from "./api/types";
import BottomBar from "./components/BottomBar";
import MapView from "./components/MapView";
import SearchPanel from "./components/SearchPanel";
import { BOUNDARY_LAYER_BY_KIND } from "./map/boundaryLayers";
import { nextSelectionColor, type SelectedBoundary } from "./map/selection";

const DEFAULT_REGION = "gva";

export default function App() {
  const [regions, setRegions] = useState<RegionMeta[]>([]);
  const [regionId, setRegionId] = useState<string>(DEFAULT_REGION);
  const [layers, setLayers] = useState<LayerMeta[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [active, setActive] = useState<Set<string>>(new Set());
  const [selections, setSelections] = useState<SelectedBoundary[]>([]);
  const [status, setStatus] = useState<string>("Loading layers...");
  // The search panel defaults to collapsed (just the icon); selecting a
  // boundary on the map opens it so the selection is visible.
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    fetchRegions()
      .then((data) => {
        setRegions(data);
        setRegionId((prev) => (data.some((r) => r.id === prev) ? prev : (data[0]?.id ?? prev)));
      })
      .catch(() => setStatus("Could not reach the API."));
  }, []);

  useEffect(() => {
    setActive(new Set());
    fetchLayers(regionId)
      .then((data) => {
        setLayers(data);
        setStatus(`${data.length} layers available`);
      })
      .catch(() => setStatus("Could not reach the API."));
    fetchSources(regionId)
      .then(setSources)
      .catch(() => setSources([]));
  }, [regionId]);

  const toggle = (layerId: string) => {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(layerId)) next.delete(layerId);
      else next.add(layerId);
      return next;
    });
  };

  // Select-all / deselect-all for a category.
  const toggleGroup = (layerIds: string[], shouldActivate: boolean) => {
    setActive((prev) => {
      const next = new Set(prev);
      for (const id of layerIds) {
        if (shouldActivate) next.add(id);
        else next.delete(id);
      }
      return next;
    });
  };

  const region = regions.find((r) => r.id === regionId) ?? null;

  const selectBoundary = (boundary: BoundarySummary) => {
    setSelections((prev) => {
      if (prev.some((s) => s.id === boundary.id)) return prev;
      const color = nextSelectionColor(prev.map((s) => s.color));
      return [...prev, { ...boundary, color }];
    });
    // Reveal the selection under the search bar, expanding it if collapsed.
    setSearchOpen(true);
    // Selecting a municipality/neighborhood shows its boundary layer so the
    // focus (dim) effect is visible.
    const boundaryLayerId = BOUNDARY_LAYER_BY_KIND[boundary.kind];
    if (boundaryLayerId) {
      setActive((prev) => (prev.has(boundaryLayerId) ? prev : new Set(prev).add(boundaryLayerId)));
    }
  };

  const removeBoundary = (boundaryId: string) => {
    setSelections((prev) => prev.filter((s) => s.id !== boundaryId));
  };

  // Cursor selection on the map: clicking a boundary toggles it.
  const toggleBoundary = (boundary: BoundarySummary) => {
    if (selections.some((s) => s.id === boundary.id)) removeBoundary(boundary.id);
    else selectBoundary(boundary);
  };

  return (
    <div className="app">
      <MapView
        layers={layers}
        active={active}
        region={region}
        selections={selections}
        onBoundaryToggle={toggleBoundary}
      />
      <BottomBar
        layers={layers}
        active={active}
        onToggle={toggle}
        onToggleGroup={toggleGroup}
        regions={regions}
        regionId={regionId}
        onRegionChange={setRegionId}
        sources={sources}
        status={status}
      />
      <SearchPanel
        selections={selections}
        onSelect={selectBoundary}
        onRemove={removeBoundary}
        open={searchOpen}
        onOpenChange={setSearchOpen}
      />
    </div>
  );
}
