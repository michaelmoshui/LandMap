import { describe, expect, it } from "vitest";

import {
  buildSelectionLayers,
  nextSelectionColor,
  SELECTION_COLORS,
  selectionSourceId,
} from "../../src/map/selection";

describe("nextSelectionColor", () => {
  it("gives each successive selection a different color", () => {
    const used: string[] = [];
    for (let i = 0; i < SELECTION_COLORS.length; i++) {
      const color = nextSelectionColor(used);
      expect(used).not.toContain(color);
      used.push(color);
    }
  });

  it("reuses a color freed by removing a selection", () => {
    const used = [...SELECTION_COLORS];
    const removed = used.splice(2, 1)[0];
    expect(nextSelectionColor(used)).toBe(removed);
  });

  it("cycles when every palette color is in use", () => {
    const used = [...SELECTION_COLORS];
    expect(nextSelectionColor(used)).toBe(SELECTION_COLORS[0]);
  });
});

describe("buildSelectionLayers", () => {
  it("creates a fill and an outline bound to the selection source", () => {
    const specs = buildSelectionLayers("hood-kitsilano", "#e6194b");
    expect(specs.map((s) => s.id)).toEqual([
      "selection-hood-kitsilano-fill",
      "selection-hood-kitsilano-outline",
    ]);
    for (const spec of specs) {
      expect(spec.source).toBe(selectionSourceId("hood-kitsilano"));
    }
    expect(specs[0].paint["fill-color"]).toBe("#e6194b");
    expect(specs[1].paint["line-color"]).toBe("#e6194b");
  });
});
