import { describe, expect, it } from "vitest";

import { BASE_MAP_STYLE } from "../../src/map/baseMapStyle";

describe("BASE_MAP_STYLE", () => {
  it("uses only vector sources (no raster tiles)", () => {
    const sources = Object.values(BASE_MAP_STYLE.sources);
    expect(sources.length).toBeGreaterThan(0);
    for (const source of sources) {
      expect(source.type).toBe("vector");
    }
  });

  it("renders building footprints", () => {
    const building = BASE_MAP_STYLE.layers.find((l) => l.id === "building");
    expect(building).toBeDefined();
    expect(building?.type).toBe("fill");
    expect(building && "source-layer" in building && building["source-layer"]).toBe("building");
  });

  it("keeps the layer set minimal for performance", () => {
    // POIs, transit, hillshading, etc. are intentionally excluded; a small
    // fixed layer budget keeps rendering fast. Raise deliberately if needed.
    expect(BASE_MAP_STYLE.layers.length).toBeLessThanOrEqual(20);
  });

  it("defines glyphs for its symbol layers", () => {
    const hasSymbols = BASE_MAP_STYLE.layers.some((l) => l.type === "symbol");
    expect(hasSymbols).toBe(true);
    expect(BASE_MAP_STYLE.glyphs).toBeTruthy();
  });

  it("includes the basic Google-Maps-style ground layers", () => {
    const ids = BASE_MAP_STYLE.layers.map((l) => l.id);
    for (const expected of ["background", "water", "park", "road-minor", "road-highway"]) {
      expect(ids).toContain(expected);
    }
  });
});
