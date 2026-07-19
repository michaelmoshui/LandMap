import { useEffect, useState } from "react";

import { searchBoundaries } from "../api/client";
import type { BoundaryKind, BoundarySummary } from "../api/types";
import type { SelectedBoundary } from "../map/selection";

const KIND_LABELS: Record<BoundaryKind, string> = {
  municipality: "Municipality",
  neighborhood: "Neighborhood",
  lot: "Lot",
};

const SEARCH_DEBOUNCE_MS = 200;

interface SearchPanelProps {
  selections: SelectedBoundary[];
  onSelect: (boundary: BoundarySummary) => void;
  onRemove: (boundaryId: string) => void;
  /** Controlled open/collapsed state (the search icon is always visible). */
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const SearchIcon = () => (
  <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">
    <path
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      d="M8.5 3a5.5 5.5 0 1 1 0 11 5.5 5.5 0 0 1 0-11zm4 9.5 4 4"
    />
  </svg>
);

export default function SearchPanel({
  selections,
  onSelect,
  onRemove,
  open,
  onOpenChange,
}: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<BoundarySummary[]>([]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    let stale = false;
    const timer = setTimeout(() => {
      searchBoundaries(query)
        .then((found) => {
          if (!stale) setResults(found);
        })
        .catch(() => {
          if (!stale) setResults([]);
        });
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      stale = true;
      clearTimeout(timer);
    };
  }, [query]);

  const selectedIds = new Set(selections.map((s) => s.id));
  const showDropdown = open && (Boolean(query.trim()) || selections.length > 0);

  return (
    <aside
      className={`search-panel${open ? " open" : " collapsed"}`}
      aria-label="Boundary search"
    >
      <div className="search-row">
        {/* Slides out to the left of the (fixed) icon; kept mounted so the
            width transition can animate in and out. */}
        <div className="search-field" aria-hidden={!open}>
          <input
            className="search-input"
            type="search"
            placeholder="Search municipalities, neighborhoods, lots..."
            aria-label="Search boundaries"
            value={query}
            disabled={!open}
            tabIndex={open ? 0 : -1}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="search-toggle"
          aria-label={open ? "Hide search" : "Show search"}
          aria-expanded={open}
          onClick={() => onOpenChange(!open)}
        >
          <SearchIcon />
        </button>
      </div>

      {showDropdown && (
        <div className="search-dropdown">
          {query.trim() && (
            <ul className="search-results" data-testid="search-results">
              {results.length === 0 && <li className="search-empty">No matches</li>}
              {results.map((boundary) => (
                <li key={boundary.id}>
                  <button
                    type="button"
                    className="search-result"
                    data-testid="search-result"
                    disabled={selectedIds.has(boundary.id)}
                    onClick={() => onSelect(boundary)}
                  >
                    <span>{boundary.name}</span>
                    <span className="kind-badge">{KIND_LABELS[boundary.kind]}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {selections.length > 0 && (
            <section>
              <div className="layer-group-title">Selected</div>
              <ul className="selected-list">
                {selections.map((selection) => (
                  <li
                    className="selected-item"
                    data-testid="selected-boundary"
                    key={selection.id}
                  >
                    {/* Municipalities/neighborhoods use the map's focus (dim)
                        effect; only lots get a highlight color. */}
                    {selection.kind === "lot" && (
                      <span className="swatch" style={{ backgroundColor: selection.color }} />
                    )}
                    <span className="selected-name">{selection.name}</span>
                    <span className="kind-badge">{KIND_LABELS[selection.kind]}</span>
                    <button
                      type="button"
                      className="remove-btn"
                      aria-label={`Remove ${selection.name}`}
                      onClick={() => onRemove(selection.id)}
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </aside>
  );
}
