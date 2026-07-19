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
    expect(baselinePoints?.paint["circle-color"]).not.toEqual(
      plannedPoints?.paint["circle-color"],
    );
  });

  it("prefers a feature's own color property over the category color", () => {
    const line = buildMapLayers("skytrain-lines", "baseline").find((s) => s.type === "line");
    expect(line?.paint["line-color"]).toEqual(["coalesce", ["get", "color"], "#2563eb"]);
  });

  it("renders stations as white circles with a line-colored ring", () => {
    const points = buildMapLayers("skytrain-stations", "baseline").find(
      (s) => s.type === "circle",
    );
    expect(points?.paint["circle-color"]).toBe("#ffffff");
    expect(points?.paint["circle-stroke-color"]).toEqual([
      "coalesce",
      ["get", "color"],
      "#2563eb",
    ]);
  });

  it("draws bus routes thinner than rail and bus stops with the TransLink gray-blue", () => {
    const busLine = buildMapLayers("bus-routes", "baseline").find((s) => s.type === "line");
    const railLine = buildMapLayers("skytrain-lines", "baseline").find((s) => s.type === "line");
    expect(busLine?.paint["line-width"]).toBeLessThan(railLine?.paint["line-width"] as number);

    const stops = buildMapLayers("bus-stops", "baseline").find((s) => s.type === "circle");
    expect(stops?.paint["circle-color"]).toEqual(["coalesce", ["get", "color"], "#7A99AC"]);
  });

  it("styles the GTA transit layers like their GVA counterparts", () => {
    const gvaStations = buildMapLayers("skytrain-stations", "baseline").find(
      (s) => s.type === "circle",
    );
    const gtaStations = buildMapLayers("gta-subway-stations", "baseline").find(
      (s) => s.type === "circle",
    );
    expect(gtaStations?.paint).toEqual(gvaStations?.paint);

    const streetcar = buildMapLayers("gta-streetcar-lines", "baseline").find(
      (s) => s.type === "line",
    );
    const subway = buildMapLayers("gta-subway-lines", "baseline").find((s) => s.type === "line");
    expect(streetcar?.paint["line-width"]).toBeLessThan(subway?.paint["line-width"] as number);
  });
});
