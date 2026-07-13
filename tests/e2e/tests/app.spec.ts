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

  test("frontend loads and shows the layer panel", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "LandMap" })).toBeVisible();
    await expect(page.getByText("Housing Prices")).toBeVisible();
  });

  test("toggling a layer requests its features", async ({ page }) => {
    const featuresRequest = page.waitForRequest((req) =>
      req.url().includes("/api/layers/housing-prices/features"),
    );
    await page.goto("/");
    await page.getByText("Housing Prices").click();
    const req = await featuresRequest;
    expect(req.url()).toContain("/api/layers/housing-prices/features");
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
    await expect(page.getByText("SkyTrain Expansion")).toBeVisible();
    await page.getByLabel("Region").selectOption("gta");
    await expect(page.getByText("Transit Expansion", { exact: true })).toBeVisible();
    await expect(page.getByText("SkyTrain Expansion")).not.toBeVisible();
  });
});
