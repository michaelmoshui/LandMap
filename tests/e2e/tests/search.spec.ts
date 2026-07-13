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

  test("searching, selecting, and removing a boundary works in the UI", async ({ page }) => {
    await page.goto("/");
    const searchBox = page.getByLabel("Search boundaries");

    const boundaryRequest = page.waitForRequest((req) =>
      req.url().includes("/api/boundaries/hood-vancouver-kerrisdale"),
    );
    await searchBox.fill("kerrisdale");
    await page.getByTestId("search-result").filter({ hasText: "Kerrisdale" }).click();
    await boundaryRequest;

    const selected = page.getByTestId("selected-boundary");
    await expect(selected).toHaveCount(1);
    await expect(selected).toContainText("Kerrisdale (Vancouver)");

    await page.getByRole("button", { name: "Remove Kerrisdale (Vancouver)" }).click();
    await expect(selected).toHaveCount(0);
  });

  test("two selections get different highlight colors", async ({ page }) => {
    await page.goto("/");
    const searchBox = page.getByLabel("Search boundaries");

    await searchBox.fill("lougheed");
    await page.getByTestId("search-result").filter({ hasText: "Lougheed" }).click();
    await searchBox.fill("coquitlam");
    await page.getByTestId("search-result").filter({ hasText: /^Coquitlam/ }).click();

    const swatches = page.getByTestId("selected-boundary").locator(".swatch");
    await expect(swatches).toHaveCount(2);
    const colors = await swatches.evaluateAll((els) =>
      els.map((el) => getComputedStyle(el).backgroundColor),
    );
    expect(new Set(colors).size).toBe(2);
  });
});
