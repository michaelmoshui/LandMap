import { describe, expect, it } from "vitest";

import {
  BOUNDARY_LAYER_BY_KIND,
  buildBoundaryLayers,
  dimFilter,
  dimLayerIdFor,
  hitLayerIdFor,
  isBoundaryLayer,
  kindForBoundaryLayer,
} from "../../src/map/boundaryLayers";
import { sourceIdFor } from "../../src/map/buildLayers";

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

describe("dimFilter", () => {
  it("dims nothing before the first selection", () => {
    expect(dimFilter([])).toEqual(["==", ["get", "id"], "__none-selected__"]);
  });

  it("dims every non-selected boundary once something is selected", () => {
    expect(dimFilter(["hood-vancouver-kerrisdale"])).toEqual([
      "!",
      ["in", ["get", "id"], ["literal", ["hood-vancouver-kerrisdale"]]],
    ]);
  });
});

describe("buildBoundaryLayers", () => {
  it("creates hit, dim, and outline layers bound to the layer source", () => {
    const specs = buildBoundaryLayers("neighborhood-boundaries", []);
    expect(specs.map((s) => s.id)).toEqual([
      hitLayerIdFor("neighborhood-boundaries"),
      dimLayerIdFor("neighborhood-boundaries"),
      "neighborhood-boundaries-outline",
    ]);
    for (const spec of specs) {
      expect(spec.source).toBe(sourceIdFor("neighborhood-boundaries"));
    }
  });

  it("keeps the hit layer invisible and the selection un-dimmed", () => {
    const selected = ["hood-burnaby-lougheed"];
    const [hit, dim] = buildBoundaryLayers("neighborhood-boundaries", selected);
    expect(hit.paint["fill-opacity"]).toBe(0);
    expect(dim.filter).toEqual(dimFilter(selected));
  });
});
