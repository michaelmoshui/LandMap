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
