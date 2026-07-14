import { describe, expect, it } from "vitest";

import { buildMapLayers, sourceIdFor } from "../../src/map/buildLayers";

describe("buildMapLayers", () => {
  it("derives a stable source id", () => {
    expect(sourceIdFor("housing-prices")).toBe("landmap-src-housing-prices");
  });

  it("creates fill, line, and point layers bound to the layer source", () => {
    const specs = buildMapLayers("skytrain-expansion", "planned");
    expect(specs).toHaveLength(3);
    // Fills first so lines/points render above polygon layers.
    expect(specs.map((s) => s.id)).toEqual([
      "skytrain-expansion-fills",
      "skytrain-expansion-lines",
      "skytrain-expansion-points",
    ]);
    for (const spec of specs) {
      expect(spec.source).toBe("landmap-src-skytrain-expansion");
    }
  });

  it("matches Multi* geometry variants in filters", () => {
    const specs = buildMapLayers("demographics", "baseline");
    const fill = specs.find((s) => s.type === "fill");
    expect(fill?.filter).toEqual(["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]]);
  });

  it("colors baseline and planned layers differently", () => {
    const baselinePoints = buildMapLayers("demographics", "baseline").find(
      (s) => s.type === "circle",
    );
    const plannedPoints = buildMapLayers("road-construction", "planned").find(
      (s) => s.type === "circle",
    );
    expect(baselinePoints?.paint["circle-color"]).not.toBe(plannedPoints?.paint["circle-color"]);
  });
});
