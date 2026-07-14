import { describe, expect, it } from "vitest";

import { popupHtml } from "../../src/map/popup";

describe("popupHtml", () => {
  it("renders properties as table rows with formatted numbers", () => {
    const html = popupHtml({
      area: "Kerrisdale",
      strata_avg_value: 1491733,
      strata_count: 1935,
    });
    expect(html).toContain("<th>area</th><td>Kerrisdale</td>");
    expect(html).toContain("<td>1,491,733</td>");
    expect(html).toContain("strata avg value");
  });

  it("skips empty values and footers the source attribution", () => {
    const html = popupHtml({
      project: "Surrey-Langley SkyTrain",
      opens: null,
      note: "",
      source: "OpenStreetMap contributors (ODbL)",
    });
    expect(html).not.toContain("opens");
    expect(html).not.toContain("note");
    expect(html).toContain('<div class="popup-source">OpenStreetMap contributors (ODbL)</div>');
    expect(html).not.toContain("<th>source</th>");
  });

  it("hides the rendering-only color property", () => {
    const html = popupHtml({ route: "Expo Line", color: "#0033A0" });
    expect(html).toContain("Expo Line");
    expect(html).not.toContain("#0033A0");
    expect(html).not.toContain("<th>color</th>");
  });

  it("escapes HTML in keys and values", () => {
    const html = popupHtml({ "<b>": '"><script>alert(1)</script>' });
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
  });
});
