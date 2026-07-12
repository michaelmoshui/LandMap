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
});
