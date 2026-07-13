import { expect, test } from "@playwright/test";

test.describe("Boundary search and selection", () => {
  test("search API matches municipalities, neighborhoods, and lots", async ({ request }) => {
    const cases: Array<[string, string]> = [
      ["coquitlam", "muni-coquitlam"],
      ["kerrisdale", "hood-vancouver-kerrisdale"],
      ["lougheed", "hood-burnaby-lougheed"],
      ["kingsway", "lot-015-632-880"],
    ];
    for (const [query, expectedId] of cases) {
      const resp = await request.get(`/api/boundaries/search?q=${query}`);
      expect(resp.ok()).toBeTruthy();
      const results = (await resp.json()) as Array<{ id: string }>;
      expect(results.map((r) => r.id)).toContain(expectedId);
    }
  });

  test("municipality boundary is a real outline, not a rectangle", async ({ request }) => {
    const resp = await request.get("/api/boundaries/muni-coquitlam");
    expect(resp.ok()).toBeTruthy();
    const feature = await resp.json();
    expect(feature.type).toBe("Feature");
    expect(["Polygon", "MultiPolygon"]).toContain(feature.geometry.type);
    const ring =
      feature.geometry.type === "MultiPolygon"
        ? feature.geometry.coordinates[0][0]
        : feature.geometry.coordinates[0];
    expect(ring.length).toBeGreaterThan(20);
  });

  test("boundary layers serve every ingested boundary", async ({ request }) => {
    const resp = await request.get("/api/layers/neighborhood-boundaries/features");
    expect(resp.ok()).toBeTruthy();
    const collection = await resp.json();
    const ids = collection.features.map(
      (f: { properties: { id: string } }) => f.properties.id,
    );
    expect(ids).toContain("hood-vancouver-kerrisdale");
    expect(ids).toContain("hood-burnaby-lougheed");
  });

  test("toggling the boundary layers requests their features", async ({ page }) => {
    const featuresRequest = page.waitForRequest((req) =>
      req.url().includes("/api/layers/neighborhood-boundaries/features"),
    );
    await page.goto("/");
    await page.getByText("Neighborhood Boundaries").click();
    await featuresRequest;
  });

  test("selecting a neighborhood enables its boundary layer for the focus effect", async ({
    page,
  }) => {
    await page.goto("/");
    const searchBox = page.getByLabel("Search boundaries");

    const layerRequest = page.waitForRequest((req) =>
      req.url().includes("/api/layers/neighborhood-boundaries/features"),
    );
    await searchBox.fill("kerrisdale");
    await page.getByTestId("search-result").filter({ hasText: "Kerrisdale" }).click();
    await layerRequest;

    await expect(page.getByRole("checkbox", { name: "Neighborhood Boundaries" })).toBeChecked();

    const selected = page.getByTestId("selected-boundary");
    await expect(selected).toHaveCount(1);
    await expect(selected).toContainText("Kerrisdale (Vancouver)");

    await page.getByRole("button", { name: "Remove Kerrisdale (Vancouver)" }).click();
    await expect(selected).toHaveCount(0);
  });

  test("selected lots keep distinct highlight colors", async ({ page }) => {
    await page.goto("/");
    const searchBox = page.getByLabel("Search boundaries");

    await searchBox.fill("kingsway");
    await page.getByTestId("search-result").filter({ hasText: "Kingsway" }).click();
    await searchBox.fill("cordova");
    await page.getByTestId("search-result").filter({ hasText: "Cordova" }).click();

    const swatches = page.getByTestId("selected-boundary").locator(".swatch");
    await expect(swatches).toHaveCount(2);
    const colors = await swatches.evaluateAll((els) =>
      els.map((el) => getComputedStyle(el).backgroundColor),
    );
    expect(new Set(colors).size).toBe(2);
  });
});
