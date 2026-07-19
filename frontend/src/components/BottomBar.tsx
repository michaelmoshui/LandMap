import { useEffect, useRef, useState } from "react";

import type { DataSource, LayerMeta, RegionMeta } from "../api/types";

/** Themed toolbar categories, Cities-Skylines-style. Order = display order. */
const GROUP_DEFS = [
  { id: "housing", label: "Housing", icon: "🏠", matches: /housing/ },
  { id: "demographics", label: "People", icon: "👥", matches: /demographic/ },
  { id: "transit", label: "Transit", icon: "🚇", matches: /transit|skytrain|subway|streetcar|bus/ },
  { id: "roads", label: "Roads", icon: "🚧", matches: /road/ },
  { id: "development", label: "Projects", icon: "🏗️", matches: /highrise|high-rise/ },
  { id: "boundaries", label: "Boundaries", icon: "🗺️", matches: /boundar/ },
] as const;

export interface ToolbarGroup {
  id: string;
  label: string;
  icon: string;
  layers: LayerMeta[];
}

export function groupLayers(layers: LayerMeta[]): ToolbarGroup[] {
  const groups: ToolbarGroup[] = GROUP_DEFS.map((def) => ({
    id: def.id,
    label: def.label,
    icon: def.icon,
    layers: [],
  }));
  const other: ToolbarGroup = { id: "other", label: "More", icon: "🧩", layers: [] };
  for (const layer of layers) {
    const index = GROUP_DEFS.findIndex((def) => def.matches.test(layer.id));
    (index === -1 ? other : groups[index]).layers.push(layer);
  }
  groups.push(other);
  return groups.filter((group) => group.layers.length > 0);
}

const SOURCES_FLYOUT = "__sources";

interface BottomBarProps {
  layers: LayerMeta[];
  active: Set<string>;
  onToggle: (layerId: string) => void;
  regions?: RegionMeta[];
  regionId?: string;
  onRegionChange?: (regionId: string) => void;
  sources?: DataSource[];
  status?: string;
}

export default function BottomBar({
  layers,
  active,
  onToggle,
  regions = [],
  regionId,
  onRegionChange,
  sources = [],
  status,
}: BottomBarProps) {
  const [open, setOpen] = useState<string | null>(null);
  const barRef = useRef<HTMLElement>(null);

  // Close the open flyout on outside click or Escape, like a game toolbar.
  useEffect(() => {
    if (open === null) return;
    const onPointerDown = (event: PointerEvent) => {
      if (barRef.current && !barRef.current.contains(event.target as Node)) setOpen(null);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(null);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const groups = groupLayers(layers);
  const toggleFlyout = (id: string) => setOpen((prev) => (prev === id ? null : id));

  return (
    <footer className="toolbar" aria-label="Map layers" ref={barRef}>
      <div className="toolbar-brand">
        <h1>LandMap</h1>
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
        {status && <p className="status">{status}</p>}
      </div>

      <div className="toolbar-divider" />

      <nav className="toolbar-groups" aria-label="Layer categories">
        {groups.map((group) => {
          const activeCount = group.layers.filter((layer) => active.has(layer.id)).length;
          return (
            <div className="toolbar-group" key={group.id}>
              {open === group.id && (
                <div className="toolbar-flyout" aria-label={`${group.label} layers`}>
                  <div className="flyout-title">{group.label}</div>
                  {group.layers.map((layer) => (
                    <label className="layer-item" key={layer.id} title={layer.description}>
                      <input
                        type="checkbox"
                        checked={active.has(layer.id)}
                        onChange={() => onToggle(layer.id)}
                      />
                      <span className="layer-title">{layer.title}</span>
                      {layer.category === "planned" && (
                        <span className="planned-badge">Planned</span>
                      )}
                    </label>
                  ))}
                </div>
              )}
              <button
                type="button"
                className={`toolbar-btn${open === group.id ? " open" : ""}${activeCount > 0 ? " has-active" : ""}`}
                aria-label={group.label}
                aria-expanded={open === group.id}
                onClick={() => toggleFlyout(group.id)}
              >
                <span className="toolbar-icon" aria-hidden="true">
                  {group.icon}
                </span>
                <span className="toolbar-btn-label" aria-hidden="true">
                  {group.label}
                </span>
                {activeCount > 0 && <span className="active-count">{activeCount}</span>}
              </button>
            </div>
          );
        })}
      </nav>

      {sources.length > 0 && (
        <>
          <div className="toolbar-divider" />
          <div className="toolbar-group">
            {open === SOURCES_FLYOUT && (
              <div className="toolbar-flyout" aria-label="Data sources">
                <div className="flyout-title">Data sources ({sources.length})</div>
                <ul className="source-list">
                  {sources.map((source) => (
                    <li key={source.id}>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        title={source.description}
                      >
                        {source.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <button
              type="button"
              className={`toolbar-btn${open === SOURCES_FLYOUT ? " open" : ""}`}
              aria-label="Data sources"
              aria-expanded={open === SOURCES_FLYOUT}
              onClick={() => toggleFlyout(SOURCES_FLYOUT)}
            >
              <span className="toolbar-icon" aria-hidden="true">
                📚
              </span>
              <span className="toolbar-btn-label" aria-hidden="true">
                Sources
              </span>
            </button>
          </div>
        </>
      )}
    </footer>
  );
}
