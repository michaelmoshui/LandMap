import { useEffect, useState } from "react";

import { fetchLayers } from "./api/client";
import type { LayerMeta } from "./api/types";
import LayerPanel from "./components/LayerPanel";
import MapView from "./components/MapView";

export default function App() {
  const [layers, setLayers] = useState<LayerMeta[]>([]);
  const [active, setActive] = useState<Set<string>>(new Set());
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

  return (
    <div className="app">
      <MapView layers={layers} active={active} />
      <LayerPanel layers={layers} active={active} onToggle={toggle} status={status} />
    </div>
  );
}
