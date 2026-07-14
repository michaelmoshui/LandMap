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
}

export default function SearchPanel({ selections, onSelect, onRemove }: SearchPanelProps) {
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

  return (
    <aside className="panel search-panel" aria-label="Boundary search">
      <input
        className="search-input"
        type="search"
        placeholder="Search municipalities, neighborhoods, lots..."
        aria-label="Search boundaries"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

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
    </aside>
  );
}
