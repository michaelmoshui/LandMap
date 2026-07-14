import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { DataSource, LayerMeta, RegionMeta } from "../../src/api/types";
import LayerPanel, { groupByCategory } from "../../src/components/LayerPanel";

const LAYERS: LayerMeta[] = [
  { id: "housing-prices", title: "Housing Prices", description: "", category: "baseline", region: "gva" },
  { id: "skytrain-expansion", title: "SkyTrain Expansion", description: "", category: "planned", region: "gva" },
];

const REGIONS: RegionMeta[] = [
  { id: "gva", title: "Greater Vancouver Area", center: [-123.02, 49.24], zoom: 10.5 },
  { id: "gta", title: "Greater Toronto Area", center: [-79.38, 43.71], zoom: 9.8 },
];

const SOURCES: DataSource[] = [
  {
    id: "metro-vancouver-portal",
    name: "Metro Vancouver Portal",
    description: "Regional hub.",
    url: "https://example.com/data",
    region: "gva",
    group: "Regional Hubs",
  },
];

describe("groupByCategory", () => {
  it("splits layers into baseline and planned", () => {
    const groups = groupByCategory(LAYERS);
    expect(groups.baseline.map((l) => l.id)).toEqual(["housing-prices"]);
    expect(groups.planned.map((l) => l.id)).toEqual(["skytrain-expansion"]);
  });
});

describe("LayerPanel", () => {
  it("renders layer titles grouped with headings", () => {
    render(<LayerPanel layers={LAYERS} active={new Set()} onToggle={() => {}} />);
    expect(screen.getByText("Housing Prices")).toBeInTheDocument();
    expect(screen.getByText("SkyTrain Expansion")).toBeInTheDocument();
    expect(screen.getByText("Baseline")).toBeInTheDocument();
    expect(screen.getByText("Planned & Upcoming")).toBeInTheDocument();
  });

  it("calls onToggle when a layer is clicked", async () => {
    const onToggle = vi.fn();
    render(<LayerPanel layers={LAYERS} active={new Set()} onToggle={onToggle} />);
    await userEvent.click(screen.getByText("Housing Prices"));
    expect(onToggle).toHaveBeenCalledWith("housing-prices");
  });

  it("reflects active layers as checked", () => {
    render(
      <LayerPanel layers={LAYERS} active={new Set(["housing-prices"])} onToggle={() => {}} />,
    );
    const checkboxes = screen.getAllByRole("checkbox");
    expect((checkboxes[0] as HTMLInputElement).checked).toBe(true);
    expect((checkboxes[1] as HTMLInputElement).checked).toBe(false);
  });

  it("renders a region selector and reports changes", async () => {
    const onRegionChange = vi.fn();
    render(
      <LayerPanel
        layers={LAYERS}
        active={new Set()}
        onToggle={() => {}}
        regions={REGIONS}
        regionId="gva"
        onRegionChange={onRegionChange}
      />,
    );
    expect(screen.getByText("Greater Vancouver Area land information")).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Region"), "gta");
    expect(onRegionChange).toHaveBeenCalledWith("gta");
  });

  it("lists data sources with links", () => {
    render(
      <LayerPanel
        layers={LAYERS}
        active={new Set()}
        onToggle={() => {}}
        regions={REGIONS}
        regionId="gva"
        sources={SOURCES}
      />,
    );
    const link = screen.getByRole("link", { name: "Metro Vancouver Portal" });
    expect(link).toHaveAttribute("href", "https://example.com/data");
  });
});
