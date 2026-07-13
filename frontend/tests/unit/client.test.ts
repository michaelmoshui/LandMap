import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchLayerFeatures, fetchLayers, fetchRegions, fetchSources } from "../../src/api/client";

afterEach(() => {
  vi.restoreAllMocks();
});

function mockFetch(body: unknown, ok = true, status = 200) {
  const fn = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("api client", () => {
  it("fetches the layer list", async () => {
    mockFetch([
      { id: "demographics", title: "Demographics", description: "", category: "baseline", region: "gva" },
    ]);
    const layers = await fetchLayers();
    expect(layers).toHaveLength(1);
    expect(layers[0].id).toBe("demographics");
  });

  it("passes the region filter to the layers endpoint", async () => {
    const fn = mockFetch([]);
    await fetchLayers("gta");
    expect(fn).toHaveBeenCalledWith("/api/layers?region=gta");
  });

  it("fetches a layer's feature collection", async () => {
    mockFetch({ type: "FeatureCollection", features: [] });
    const fc = await fetchLayerFeatures("demographics");
    expect(fc.type).toBe("FeatureCollection");
  });

  it("fetches the region list", async () => {
    const fn = mockFetch([
      { id: "gva", title: "Greater Vancouver Area", center: [-123.02, 49.24], zoom: 10.5 },
    ]);
    const regions = await fetchRegions();
    expect(fn).toHaveBeenCalledWith("/api/regions");
    expect(regions[0].id).toBe("gva");
  });

  it("fetches data sources for a region", async () => {
    const fn = mockFetch([
      {
        id: "metro-vancouver",
        name: "Metro Vancouver",
        description: "",
        url: "https://example.com",
        region: "gva",
        group: "",
      },
    ]);
    const sources = await fetchSources("gva");
    expect(fn).toHaveBeenCalledWith("/api/sources?region=gva");
    expect(sources[0].url).toBe("https://example.com");
  });

  it("throws on a failed request", async () => {
    mockFetch(null, false, 500);
    await expect(fetchLayers()).rejects.toThrow(/Request failed/);
  });
});
