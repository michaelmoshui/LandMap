import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchBoundary,
  fetchLayerFeatures,
  fetchLayers,
  searchBoundaries,
} from "../../src/api/client";

afterEach(() => {
  vi.restoreAllMocks();
});

function mockFetch(body: unknown, ok = true, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok,
      status,
      json: async () => body,
    }),
  );
}

describe("api client", () => {
  it("fetches the layer list", async () => {
    mockFetch([{ id: "demographics", title: "Demographics", description: "", category: "baseline" }]);
    const layers = await fetchLayers();
    expect(layers).toHaveLength(1);
    expect(layers[0].id).toBe("demographics");
  });

  it("fetches a layer's feature collection", async () => {
    mockFetch({ type: "FeatureCollection", features: [] });
    const fc = await fetchLayerFeatures("demographics");
    expect(fc.type).toBe("FeatureCollection");
  });

  it("throws on a failed request", async () => {
    mockFetch(null, false, 500);
    await expect(fetchLayers()).rejects.toThrow(/Request failed/);
  });

  it("searches boundaries with an encoded query", async () => {
    mockFetch([{ id: "hood-kitsilano", name: "Kitsilano", kind: "neighborhood" }]);
    const results = await searchBoundaries("kits & more");
    expect(results[0].id).toBe("hood-kitsilano");
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).toContain("/boundaries/search?q=kits%20%26%20more");
  });

  it("fetches a boundary feature", async () => {
    mockFetch({ type: "Feature", geometry: { type: "Polygon", coordinates: [] }, properties: {} });
    const feature = await fetchBoundary("muni-vancouver");
    expect(feature.type).toBe("Feature");
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).toContain("/boundaries/muni-vancouver");
  });
});
