import { useEffect, useState } from "react";

import { fetchLayers, fetchRegions, fetchSources } from "./api/client";
import type { DataSource, LayerMeta, RegionMeta } from "./api/types";
import LayerPanel from "./components/LayerPanel";
import MapView from "./components/MapView";

const DEFAULT_REGION = "gva";

export default function App() {
  const [regions, setRegions] = useState<RegionMeta[]>([]);
  const [regionId, setRegionId] = useState<string>(DEFAULT_REGION);
  const [layers, setLayers] = useState<LayerMeta[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [active, setActive] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<string>("Loading layers...");

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

  const region = regions.find((r) => r.id === regionId) ?? null;

  return (
    <div className="app">
      <MapView layers={layers} active={active} region={region} />
      <LayerPanel
        layers={layers}
        active={active}
        onToggle={toggle}
        regions={regions}
        regionId={regionId}
        onRegionChange={setRegionId}
        sources={sources}
        status={status}
      />
    </div>
  );
}
