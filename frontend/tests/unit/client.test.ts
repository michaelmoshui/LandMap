import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchLayerFeatures, fetchLayers } from "../../src/api/client";

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
});
