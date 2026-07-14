import { expect, test } from "@playwright/test";

test.describe("LandMap end-to-end", () => {
  test("backend health endpoint is reachable through the proxy", async ({ request }) => {
    const resp = await request.get("/api/health");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });

  test("layers API returns the expected layers", async ({ request }) => {
    const resp = await request.get("/api/layers");
    expect(resp.ok()).toBeTruthy();
    const layers = (await resp.json()) as Array<{ id: string }>;
    const ids = layers.map((l) => l.id);
    expect(ids).toContain("housing-prices");
    expect(ids).toContain("skytrain-expansion");
    expect(ids).toContain("skytrain-lines");
    expect(ids).toContain("skytrain-stations");
    expect(ids).toContain("bus-routes");
    expect(ids).toContain("bus-stops");
    expect(ids).toContain("seabus-wce");
  });

  test("frontend loads and shows the layer toolbar", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "LandMap" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Housing" })).toBeVisible();
    await page.getByRole("button", { name: "Housing" }).click();
    await expect(page.getByText("Housing Prices")).toBeVisible();
  });

  test("toggling a layer requests its features", async ({ page }) => {
    const featuresRequest = page.waitForRequest((req) =>
      req.url().includes("/api/layers/housing-prices/features"),
    );
    await page.goto("/");
    await page.getByRole("button", { name: "Housing" }).click();
    await page.getByText("Housing Prices").click();
    const req = await featuresRequest;
    expect(req.url()).toContain("/api/layers/housing-prices/features");
  });

  test("GVA layers serve ingested real data", async ({ request }) => {
    // housing-prices: one polygon per Vancouver local area with assessed values.
    const housing = await (await request.get("/api/layers/housing-prices/features")).json();
    expect(housing.features.length).toBeGreaterThanOrEqual(20);
    const housingProps = housing.features[0].properties;
    expect(housingProps).toHaveProperty("area");
    expect(housingProps).toHaveProperty("strata_avg_value");

    // demographics: census population per Metro Vancouver municipality.
    const demo = await (await request.get("/api/layers/demographics/features")).json();
    const vancouver = demo.features.find(
      (f: { properties: { municipality: string } }) => f.properties.municipality === "Vancouver",
    );
    expect(vancouver.properties.population_2021).toBeGreaterThan(500000);
  });

  test("transit layers serve the TransLink network in official colours", async ({ request }) => {
    // SkyTrain lines carry TransLink's official route colours from GTFS.
    const lines = await (await request.get("/api/layers/skytrain-lines/features")).json();
    const colors = new Set(lines.features.map((f: { properties: { color: string } }) => f.properties.color));
    expect(colors).toContain("#0033A0"); // Expo Line
    expect(colors).toContain("#FFCD00"); // Millennium Line
    expect(colors).toContain("#007C9F"); // Canada Line

    // Stations include the interchange hub and name the lines serving it.
    const stations = await (await request.get("/api/layers/skytrain-stations/features")).json();
    const waterfront = stations.features.find(
      (f: { properties: { station: string } }) => f.properties.station === "Waterfront Station",
    );
    expect(waterfront).toBeTruthy();

    // The full bus network: hundreds of routes, thousands of stops.
    const routes = await (await request.get("/api/layers/bus-routes/features")).json();
    expect(routes.features.length).toBeGreaterThanOrEqual(200);
    const stops = await (await request.get("/api/layers/bus-stops/features")).json();
    expect(stops.features.length).toBeGreaterThanOrEqual(5000);

    // SeaBus & West Coast Express render as their own layer.
    const seabus = await (await request.get("/api/layers/seabus-wce/features")).json();
    const modes = new Set(seabus.features.map((f: { properties: { mode?: string } }) => f.properties.mode));
    expect(modes).toContain("Ferry");
    expect(modes).toContain("Commuter Rail");
  });

  test("toggling SkyTrain lines from the Transit flyout requests its features", async ({ page }) => {
    const featuresRequest = page.waitForRequest((req) =>
      req.url().includes("/api/layers/skytrain-lines/features"),
    );
    await page.goto("/");
    await page.getByRole("button", { name: "Transit" }).click();
    await page.getByText("SkyTrain Lines", { exact: true }).click();
    const req = await featuresRequest;
    expect(req.url()).toContain("/api/layers/skytrain-lines/features");
  });

  test("regions API lists Vancouver and Toronto", async ({ request }) => {
    const resp = await request.get("/api/regions");
    expect(resp.ok()).toBeTruthy();
    const regions = (await resp.json()) as Array<{ id: string; center: number[] }>;
    const ids = regions.map((r) => r.id);
    expect(ids).toContain("gva");
    expect(ids).toContain("gta");
    for (const region of regions) {
      expect(region.center).toHaveLength(2);
    }
  });

  test("sources API serves entries parsed from SOURCES.md", async ({ request }) => {
    const resp = await request.get("/api/sources?region=gta");
    expect(resp.ok()).toBeTruthy();
    const sources = (await resp.json()) as Array<{ url: string; region: string }>;
    expect(sources.length).toBeGreaterThan(0);
    for (const source of sources) {
      expect(source.region).toBe("gta");
      expect(source.url).toMatch(/^https?:\/\//);
    }
  });

  test("switching to Toronto shows GTA layers", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Transit" }).click();
    await expect(page.getByText("SkyTrain Expansion")).toBeVisible();
    // The flyout stays open across the region switch and re-renders with GTA layers.
    await page.getByLabel("Region").selectOption("gta");
    await expect(page.getByText("Transit Expansion", { exact: true })).toBeVisible();
    await expect(page.getByText("SkyTrain Expansion")).not.toBeVisible();
  });
});
