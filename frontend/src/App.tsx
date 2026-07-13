import { useEffect, useState } from "react";

import { fetchLayers } from "./api/client";
import type { BoundarySummary, LayerMeta } from "./api/types";
import LayerPanel from "./components/LayerPanel";
import MapView from "./components/MapView";
import SearchPanel from "./components/SearchPanel";
import { nextSelectionColor, type SelectedBoundary } from "./map/selection";

export default function App() {
  const [layers, setLayers] = useState<LayerMeta[]>([]);
  const [active, setActive] = useState<Set<string>>(new Set());
  const [selections, setSelections] = useState<SelectedBoundary[]>([]);
  const [status, setStatus] = useState<string>("Loading layers...");

  useEffect(() => {
    fetchLayers()
      .then((data) => {
        setLayers(data);
        setStatus(`${data.length} layers available`);
      })
      .catch(() => setStatus("Could not reach the API."));
  }, []);

  const toggle = (layerId: string) => {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(layerId)) next.delete(layerId);
      else next.add(layerId);
      return next;
    });
  };

  const selectBoundary = (boundary: BoundarySummary) => {
    setSelections((prev) => {
      if (prev.some((s) => s.id === boundary.id)) return prev;
      const color = nextSelectionColor(prev.map((s) => s.color));
      return [...prev, { ...boundary, color }];
    });
  };

  const removeBoundary = (boundaryId: string) => {
    setSelections((prev) => prev.filter((s) => s.id !== boundaryId));
  };

  return (
    <div className="app">
      <MapView layers={layers} active={active} selections={selections} />
      <LayerPanel layers={layers} active={active} onToggle={toggle} status={status} />
      <SearchPanel selections={selections} onSelect={selectBoundary} onRemove={removeBoundary} />
    </div>
  );
}
