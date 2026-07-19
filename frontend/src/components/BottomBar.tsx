import { useEffect, useRef, useState } from "react";

import type { DataSource, LayerMeta, RegionMeta } from "../api/types";

/** Themed toolbar categories, Cities-Skylines-style. Order = display order. */
const GROUP_DEFS = [
  { id: "housing", label: "Housing", icon: "🏠", matches: /housing/ },
  { id: "transit", label: "Transit", icon: "🚇", matches: /transit|skytrain|subway|streetcar|bus/ },
  { id: "roads", label: "Roads", icon: "🚧", matches: /road/ },
  { id: "development", label: "Projects", icon: "🏗️", matches: /highrise|high-rise/ },
  // City Info (the demographics layer) lives with the boundary layers.
  { id: "boundaries", label: "Boundaries", icon: "🗺️", matches: /boundar|demographic/ },
] as const;

/** Where a flyout should anchor relative to its toolbar button. */
export type FlyoutAlignment = "left" | "center" | "right";

/**
 * Pick a flyout anchor from the button's on-screen position so it never spills
 * off the page: buttons near the right edge open right-aligned, near the left
 * edge left-aligned, and anything in the middle stays centered.
 */
export function flyoutAlignment(
  buttonRect: { left: number; right: number },
  viewportWidth: number,
): FlyoutAlignment {
  const center = (buttonRect.left + buttonRect.right) / 2;
  if (center > viewportWidth * 0.66) return "right";
  if (center < viewportWidth * 0.34) return "left";
  return "center";
}

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
  onToggleGroup?: (layerIds: string[], active: boolean) => void;
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
  onToggleGroup,
  regions = [],
  regionId,
  onRegionChange,
  sources = [],
  status,
}: BottomBarProps) {
  const [open, setOpen] = useState<string | null>(null);
  const [alignment, setAlignment] = useState<FlyoutAlignment>("center");
  const barRef = useRef<HTMLElement>(null);
  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({});

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

  // Anchor the open flyout to its button so it can't spill off the page edge.
  useEffect(() => {
    if (open === null) return;
    const measure = () => {
      const button = buttonRefs.current[open];
      if (button) setAlignment(flyoutAlignment(button.getBoundingClientRect(), window.innerWidth));
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
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
          const allActive = activeCount === group.layers.length && group.layers.length > 0;
          return (
            <div className="toolbar-group" key={group.id}>
              {open === group.id && (
                <div
                  className={`toolbar-flyout flyout-align-${alignment}`}
                  aria-label={`${group.label} layers`}
                >
                  <div className="flyout-title">{group.label}</div>
                  <label className="layer-item select-all">
                    <input
                      type="checkbox"
                      checked={allActive}
                      ref={(el) => {
                        if (el) el.indeterminate = activeCount > 0 && !allActive;
                      }}
                      onChange={() =>
                        onToggleGroup?.(
                          group.layers.map((layer) => layer.id),
                          !allActive,
                        )
                      }
                    />
                    <span className="layer-title">Select all</span>
                  </label>
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
                ref={(el) => {
                  buttonRefs.current[group.id] = el;
                }}
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
              <div
                className={`toolbar-flyout flyout-align-${alignment}`}
                aria-label="Data sources"
              >
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
              ref={(el) => {
                buttonRefs.current[SOURCES_FLYOUT] = el;
              }}
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
