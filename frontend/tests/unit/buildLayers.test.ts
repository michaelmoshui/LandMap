import { describe, expect, it } from "vitest";

import { buildMapLayers, sourceIdFor } from "../../src/map/buildLayers";

describe("buildMapLayers", () => {
  it("derives a stable source id", () => {
    expect(sourceIdFor("housing-prices")).toBe("landmap-src-housing-prices");
  });

  it("creates point and line layers bound to the layer source", () => {
    const specs = buildMapLayers("skytrain-expansion", "planned");
    expect(specs).toHaveLength(2);
    expect(specs.map((s) => s.id)).toEqual([
      "skytrain-expansion-points",
      "skytrain-expansion-lines",
    ]);
    for (const spec of specs) {
      expect(spec.source).toBe("landmap-src-skytrain-expansion");
    }
  });

  it("colors baseline and planned layers differently", () => {
    const baseline = buildMapLayers("demographics", "baseline");
    const planned = buildMapLayers("road-construction", "planned");
    expect(baseline[0].paint["circle-color"]).not.toBe(planned[0].paint["circle-color"]);
  });
});
