import { describe, expect, it } from "vitest";

import type { GeoFeature } from "../../src/api/types";
import {
  BOUNDARY_LAYER_BY_KIND,
  buildBoundaryLayers,
  buildDimMask,
  dimLayerIdFor,
  hitLayerIdFor,
  isBoundaryLayer,
  kindForBoundaryLayer,
  maskSourceIdFor,
} from "../../src/map/boundaryLayers";
import { sourceIdFor } from "../../src/map/buildLayers";

const BRENTWOOD: GeoFeature = {
  type: "Feature",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [-123.01, 49.26],
        [-122.99, 49.26],
        [-122.99, 49.28],
        [-123.01, 49.28],
        [-123.01, 49.26],
      ],
    ],
  },
  properties: { id: "hood-burnaby-brentwood", name: "Brentwood (Burnaby)", kind: "neighborhood" },
};

describe("boundary layer identification", () => {
  it("maps municipality and neighborhood kinds to layer ids, but not lots", () => {
    expect(BOUNDARY_LAYER_BY_KIND.municipality).toBe("municipality-boundaries");
    expect(BOUNDARY_LAYER_BY_KIND.neighborhood).toBe("neighborhood-boundaries");
    expect(BOUNDARY_LAYER_BY_KIND.lot).toBeUndefined();
    expect(isBoundaryLayer("neighborhood-boundaries")).toBe(true);
    expect(isBoundaryLayer("housing-prices")).toBe(false);
    expect(kindForBoundaryLayer("municipality-boundaries")).toBe("municipality");
  });
});

describe("buildDimMask", () => {
  it("dims nothing before the first selection", () => {
    expect(buildDimMask([]).features).toHaveLength(0);
  });

  it("dims the whole world except the selected shapes", () => {
    const mask = buildDimMask([BRENTWOOD]);
    expect(mask.features).toHaveLength(1);
    const coords = mask.features[0].geometry.coordinates as number[][][][];
    const [worldRing, ...cutouts] = coords[0];
    expect(worldRing[0]).toEqual([-180, -85]);
    expect(cutouts).toEqual(BRENTWOOD.geometry.coordinates);
  });

  it("keeps holes inside a selected shape dimmed", () => {
    const withHole: GeoFeature = {
      ...BRENTWOOD,
      geometry: {
        type: "Polygon",
        coordinates: [
          (BRENTWOOD.geometry.coordinates as number[][][])[0],
          [
            [-123.005, 49.265],
            [-122.995, 49.265],
            [-122.995, 49.275],
            [-123.005, 49.265],
          ],
        ],
      },
    };
    const coords = buildDimMask([withHole]).features[0].geometry.coordinates as number[][][][];
    expect(coords).toHaveLength(2);
    expect(coords[1][0][0]).toEqual([-123.005, 49.265]);
  });
});

describe("buildBoundaryLayers", () => {
  it("creates hit, dim, and outline layers", () => {
    const specs = buildBoundaryLayers("neighborhood-boundaries");
    expect(specs.map((s) => s.id)).toEqual([
      hitLayerIdFor("neighborhood-boundaries"),
      dimLayerIdFor("neighborhood-boundaries"),
      "neighborhood-boundaries-outline",
    ]);
  });

  it("binds hit and outline to the data source, and dim to the mask source", () => {
    const [hit, dim, outline] = buildBoundaryLayers("neighborhood-boundaries");
    expect(hit.source).toBe(sourceIdFor("neighborhood-boundaries"));
    expect(outline.source).toBe(sourceIdFor("neighborhood-boundaries"));
    expect(dim.source).toBe(maskSourceIdFor("neighborhood-boundaries"));
    expect(hit.paint["fill-opacity"]).toBe(0);
  });
});
