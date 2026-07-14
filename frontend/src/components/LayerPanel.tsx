import type { DataSource, LayerCategory, LayerMeta, RegionMeta } from "../api/types";

const GROUP_LABELS: Record<LayerCategory, string> = {
  baseline: "Baseline",
  planned: "Planned & Upcoming",
};

interface LayerPanelProps {
  layers: LayerMeta[];
  active: Set<string>;
  onToggle: (layerId: string) => void;
  regions?: RegionMeta[];
  regionId?: string;
  onRegionChange?: (regionId: string) => void;
  sources?: DataSource[];
  status?: string;
}

export function groupByCategory(layers: LayerMeta[]): Record<LayerCategory, LayerMeta[]> {
  const groups: Record<LayerCategory, LayerMeta[]> = { baseline: [], planned: [] };
  for (const layer of layers) {
    groups[layer.category].push(layer);
  }
  return groups;
}

export default function LayerPanel({
  layers,
  active,
  onToggle,
  regions = [],
  regionId,
  onRegionChange,
  sources = [],
  status,
}: LayerPanelProps) {
  const groups = groupByCategory(layers);
  const region = regions.find((r) => r.id === regionId);
  return (
    <aside className="panel" aria-label="Map layers">
      <h1>LandMap</h1>
      <p className="subtitle">{region ? `${region.title} land information` : "Land information"}</p>

      {regions.length > 0 && (
        <select
          className="region-select"
          aria-label="Region"
          value={regionId}
          onChange={(event) => onRegionChange?.(event.target.value)}
        >
          {regions.map((r) => (
            <option key={r.id} value={r.id}>
              {r.title}
            </option>
          ))}
        </select>
      )}

      {(Object.keys(groups) as LayerCategory[]).map((category) =>
        groups[category].length === 0 ? null : (
          <section key={category}>
            <div className="layer-group-title">{GROUP_LABELS[category]}</div>
            {groups[category].map((layer) => (
              <label className="layer-item" key={layer.id} title={layer.description}>
                <input
                  type="checkbox"
                  checked={active.has(layer.id)}
                  onChange={() => onToggle(layer.id)}
                />
                {layer.title}
              </label>
            ))}
          </section>
        ),
      )}

      {sources.length > 0 && (
        <details className="sources">
          <summary className="layer-group-title">Data sources ({sources.length})</summary>
          <ul className="source-list">
            {sources.map((source) => (
              <li key={source.id}>
                <a href={source.url} target="_blank" rel="noreferrer" title={source.description}>
                  {source.name}
                </a>
              </li>
            ))}
          </ul>
        </details>
      )}

      {status && <p className="status">{status}</p>}
    </aside>
  );
}
