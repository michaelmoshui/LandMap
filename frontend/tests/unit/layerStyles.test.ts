import { describe, expect, it } from "vitest";

import type { FeatureCollection, GeoFeature } from "../../src/api/types";
import { assignCityColors, CITY_COLORS, isCityInfoLayer } from "../../src/map/layerStyles";

// A unit square [x, x+1] x [0, 1]. Neighbours share the vertical edge, so
// square(x) and square(x+1) are detected as adjacent via their shared corners.
function square(name: string, x: number, color?: string): GeoFeature {
  const ring = [
    [x, 0],
    [x + 1, 0],
    [x + 1, 1],
    [x, 1],
    [x, 0],
  ];
  return {
    type: "Feature",
    geometry: { type: "Polygon", coordinates: [ring] },
    properties: color ? { municipality: name, color } : { municipality: name },
  };
}

// A polygon with no shared vertices with any other feature (far away).
function isolated(name: string, color?: string): GeoFeature {
  return square(name, 1000, color);
}

function collection(features: GeoFeature[]): FeatureCollection {
  return { type: "FeatureCollection", features };
}

function colorsOf(fc: FeatureCollection): (string | undefined)[] {
  return fc.features.map((f) => f.properties.color as string | undefined);
}

describe("isCityInfoLayer", () => {
  it("matches the GVA and GTA demographics layers only", () => {
    expect(isCityInfoLayer("demographics")).toBe(true);
    expect(isCityInfoLayer("gta-demographics")).toBe(true);
    expect(isCityInfoLayer("housing-prices")).toBe(false);
    expect(isCityInfoLayer("municipality-boundaries")).toBe(false);
  });
});

describe("assignCityColors", () => {
  it("gives every adjacent city a different colour", () => {
    // A chain A-B-C-D where each touches the next.
    const result = assignCityColors(
      collection([square("A", 0), square("B", 1), square("C", 2), square("D", 3)]),
    );
    const colors = colorsOf(result);
    // Adjacent pairs must differ.
    expect(colors[0]).not.toBe(colors[1]);
    expect(colors[1]).not.toBe(colors[2]);
    expect(colors[2]).not.toBe(colors[3]);
    // All from the palette.
    for (const color of colors) expect(CITY_COLORS).toContain(color);
  });

  it("reuses colours for non-adjacent cities (only 2 needed for a chain)", () => {
    const result = assignCityColors(
      collection([square("A", 0), square("B", 1), square("C", 2)]),
    );
    const colors = colorsOf(result);
    // A and C do not touch, so the greedy colourer reuses A's colour for C.
    expect(colors[0]).toBe(colors[2]);
    expect(colors[0]).not.toBe(colors[1]);
  });

  it("keeps a feature's own colour and constrains its neighbours", () => {
    const result = assignCityColors(
      collection([square("A", 0), square("Custom", 1, "#123456"), square("B", 2)]),
    );
    const colors = colorsOf(result);
    expect(colors[1]).toBe("#123456");
    // A and B border the custom-coloured city, so neither may use #123456.
    expect(colors[0]).not.toBe("#123456");
    expect(colors[2]).not.toBe("#123456");
  });

  it("assigns the first palette colour to isolated cities", () => {
    const result = assignCityColors(collection([isolated("A")]));
    expect(colorsOf(result)).toEqual([CITY_COLORS[0]]);
  });

  it("does not mutate the input collection", () => {
    const input = collection([square("A", 0)]);
    assignCityColors(input);
    expect(input.features[0].properties.color).toBeUndefined();
  });
});
