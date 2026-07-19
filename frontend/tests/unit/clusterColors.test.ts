import { describe, expect, it } from "vitest";

import type { FeatureCollection, GeoFeature } from "../../src/api/types";
import {
  assignClusterColors,
  CLUSTER_COLORS,
  featureCentroid,
  haversineKm,
  isClusteredLayer,
} from "../../src/map/clusterColors";

function lineFeature(
  coords: number[][],
  props: Record<string, unknown> = {},
): GeoFeature {
  return {
    type: "Feature",
    geometry: { type: "LineString", coordinates: coords },
    properties: props,
  };
}

function collection(features: GeoFeature[]): FeatureCollection {
  return { type: "FeatureCollection", features };
}

// A short line centred near [lng, lat], tagged with a unique url so each is its
// own cluster.
function near(lng: number, lat: number, url: string): GeoFeature {
  return lineFeature(
    [
      [lng, lat],
      [lng + 0.0005, lat + 0.0005],
    ],
    { url, project: "Various Locations" },
  );
}

describe("isClusteredLayer", () => {
  it("matches the road-construction layers only", () => {
    expect(isClusteredLayer("road-construction")).toBe(true);
    expect(isClusteredLayer("gta-road-construction")).toBe(true);
    expect(isClusteredLayer("skytrain-lines")).toBe(false);
    expect(isClusteredLayer("demographics")).toBe(false);
  });
});

describe("haversineKm", () => {
  it("is ~0 for identical points", () => {
    expect(haversineKm([-123, 49], [-123, 49])).toBeCloseTo(0, 5);
  });

  it("measures a realistic distance", () => {
    // ~1 degree of latitude is ~111 km.
    expect(haversineKm([-123, 49], [-123, 50])).toBeGreaterThan(110);
    expect(haversineKm([-123, 49], [-123, 50])).toBeLessThan(112);
  });
});

describe("featureCentroid", () => {
  it("averages LineString positions", () => {
    const centroid = featureCentroid(
      lineFeature([
        [0, 0],
        [2, 4],
      ]),
    );
    expect(centroid).toEqual([1, 2]);
  });

  it("handles MultiLineString nesting", () => {
    const feature: GeoFeature = {
      type: "Feature",
      geometry: {
        type: "MultiLineString",
        coordinates: [
          [
            [0, 0],
            [0, 2],
          ],
          [
            [4, 0],
            [4, 2],
          ],
        ],
      },
      properties: {},
    };
    expect(featureCentroid(feature)).toEqual([2, 1]);
  });

  it("returns null for empty geometry", () => {
    const feature: GeoFeature = {
      type: "Feature",
      geometry: { type: "LineString", coordinates: [] },
      properties: {},
    };
    expect(featureCentroid(feature)).toBeNull();
  });
});

describe("assignClusterColors", () => {
  it("gives two nearby clusters different colours", () => {
    // Two projects a few hundred metres apart (well within the 2km threshold).
    const result = assignClusterColors(
      collection([near(-123.15, 49.27, "a"), near(-123.149, 49.271, "b")]),
    );
    const colors = result.features.map((f) => f.properties.color);
    expect(colors[0]).not.toEqual(colors[1]);
    for (const c of colors) expect(CLUSTER_COLORS).toContain(c);
  });

  it("lets far-apart clusters reuse the first colour", () => {
    // Downtown Vancouver vs. central Surrey: ~20km apart, not adjacent.
    const result = assignClusterColors(
      collection([near(-123.12, 49.28, "a"), near(-122.8, 49.19, "b")]),
    );
    const colors = result.features.map((f) => f.properties.color);
    expect(colors[0]).toEqual(CLUSTER_COLORS[0]);
    expect(colors[1]).toEqual(CLUSTER_COLORS[0]);
  });

  it("keeps features of the same project (same url) in one colour", () => {
    const result = assignClusterColors(
      collection([
        near(-123.15, 49.27, "same"),
        near(-123.1502, 49.2702, "same"),
        near(-123.149, 49.271, "other"),
      ]),
    );
    const colors = result.features.map((f) => f.properties.color);
    expect(colors[0]).toEqual(colors[1]); // same project
    expect(colors[0]).not.toEqual(colors[2]); // different, nearby project
  });

  it("gives three mutually-close clusters three distinct colours", () => {
    const result = assignClusterColors(
      collection([
        near(-123.15, 49.27, "a"),
        near(-123.1505, 49.2705, "b"),
        near(-123.1495, 49.2695, "c"),
      ]),
    );
    const colors = new Set(result.features.map((f) => f.properties.color));
    expect(colors.size).toBe(3);
  });

  it("respects a feature's own colour", () => {
    const result = assignClusterColors(
      collection([near(-123.15, 49.27, "a"), lineFeature([[-123.149, 49.271], [-123.148, 49.272]], { url: "b", color: "#123456" })]),
    );
    expect(result.features[1].properties.color).toBe("#123456");
  });

  it("does not mutate the input", () => {
    const input = collection([near(-123.15, 49.27, "a")]);
    assignClusterColors(input);
    expect(input.features[0].properties.color).toBeUndefined();
  });
});
