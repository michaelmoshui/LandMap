import type { LayerCategory, LayerMeta } from "../api/types";

const GROUP_LABELS: Record<LayerCategory, string> = {
  baseline: "Baseline",
  planned: "Planned & Upcoming",
};

interface LayerPanelProps {
  layers: LayerMeta[];
  active: Set<string>;
  onToggle: (layerId: string) => void;
  status?: string;
}

export function groupByCategory(layers: LayerMeta[]): Record<LayerCategory, LayerMeta[]> {
  const groups: Record<LayerCategory, LayerMeta[]> = { baseline: [], planned: [] };
  for (const layer of layers) {
    groups[layer.category].push(layer);
  }
  return groups;
}

export default function LayerPanel({ layers, active, onToggle, status }: LayerPanelProps) {
  const groups = groupByCategory(layers);
  return (
    <aside className="panel" aria-label="Map layers">
      <h1>LandMap</h1>
      <p className="subtitle">Greater Vancouver land information</p>

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

      {status && <p className="status">{status}</p>}
    </aside>
  );
}
