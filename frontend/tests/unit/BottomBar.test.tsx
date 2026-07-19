import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { DataSource, LayerMeta, RegionMeta } from "../../src/api/types";
import BottomBar, { flyoutAlignment, groupLayers } from "../../src/components/BottomBar";

const LAYERS: LayerMeta[] = [
  { id: "housing-prices", title: "Housing Prices", description: "", category: "baseline", region: "gva" },
  { id: "skytrain-expansion", title: "SkyTrain Expansion", description: "", category: "planned", region: "gva" },
  { id: "neighborhood-boundaries", title: "Neighborhood Boundaries", description: "", category: "baseline", region: "gva" },
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

describe("groupLayers", () => {
  it("assigns layers to themed toolbar groups", () => {
    const groups = groupLayers(LAYERS);
    expect(groups.map((g) => g.id)).toEqual(["housing", "transit", "boundaries"]);
    expect(groups[0].layers.map((l) => l.id)).toEqual(["housing-prices"]);
  });

  it("groups the TransLink and TTC/GO transit layers under Transit", () => {
    const transit: LayerMeta[] = [
      "skytrain-lines",
      "skytrain-stations",
      "bus-routes",
      "bus-stops",
      "seabus-wce",
      "gta-subway-lines",
      "gta-subway-stations",
      "gta-streetcar-lines",
      "gta-bus-routes",
      "gta-bus-stops",
      "gta-go-transit",
    ].map((id) => ({ id, title: id, description: "", category: "baseline", region: "gva" }));
    const groups = groupLayers(transit);
    expect(groups).toHaveLength(1);
    expect(groups[0].id).toBe("transit");
    expect(groups[0].layers).toHaveLength(11);
  });

  it("puts unrecognized layers in the More group and drops empty groups", () => {
    const layer: LayerMeta = {
      id: "mystery-layer",
      title: "Mystery",
      description: "",
      category: "baseline",
      region: "gva",
    };
    const groups = groupLayers([layer]);
    expect(groups).toHaveLength(1);
    expect(groups[0].id).toBe("other");
    expect(groups[0].layers).toEqual([layer]);
  });

  it("groups the demographics (City Info) layer under Boundaries", () => {
    const layers: LayerMeta[] = [
      { id: "demographics", title: "City Info", description: "", category: "baseline", region: "gva" },
      { id: "municipality-boundaries", title: "Municipality Boundaries", description: "", category: "baseline", region: "gva" },
    ];
    const groups = groupLayers(layers);
    expect(groups.map((g) => g.id)).toEqual(["boundaries"]);
    expect(groups[0].layers.map((l) => l.id)).toEqual(["demographics", "municipality-boundaries"]);
  });
});

describe("flyoutAlignment", () => {
  it("right-aligns buttons near the right edge", () => {
    expect(flyoutAlignment({ left: 900, right: 960 }, 1000)).toBe("right");
  });

  it("left-aligns buttons near the left edge", () => {
    expect(flyoutAlignment({ left: 40, right: 100 }, 1000)).toBe("left");
  });

  it("centers buttons in the middle of the viewport", () => {
    expect(flyoutAlignment({ left: 470, right: 530 }, 1000)).toBe("center");
  });
});

describe("BottomBar", () => {
  it("renders one toolbar button per non-empty group", () => {
    render(<BottomBar layers={LAYERS} active={new Set()} onToggle={() => {}} />);
    expect(screen.getByRole("button", { name: "Housing" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Transit" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Boundaries" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Roads" })).not.toBeInTheDocument();
    // Layer toggles stay hidden until a category is opened.
    expect(screen.queryByText("Housing Prices")).not.toBeInTheDocument();
  });

  it("opens a flyout with the group's layers and toggles them", async () => {
    const onToggle = vi.fn();
    render(<BottomBar layers={LAYERS} active={new Set()} onToggle={onToggle} />);
    await userEvent.click(screen.getByRole("button", { name: "Housing" }));
    await userEvent.click(screen.getByText("Housing Prices"));
    expect(onToggle).toHaveBeenCalledWith("housing-prices");
  });

  it("closes the flyout when the same button is clicked again", async () => {
    render(<BottomBar layers={LAYERS} active={new Set()} onToggle={() => {}} />);
    const button = screen.getByRole("button", { name: "Housing" });
    await userEvent.click(button);
    expect(screen.getByText("Housing Prices")).toBeInTheDocument();
    await userEvent.click(button);
    expect(screen.queryByText("Housing Prices")).not.toBeInTheDocument();
  });

  it("reflects active layers as checked and shows a count badge", async () => {
    render(
      <BottomBar layers={LAYERS} active={new Set(["housing-prices"])} onToggle={() => {}} />,
    );
    const housingButton = screen.getByRole("button", { name: "Housing" });
    expect(housingButton.querySelector(".active-count")?.textContent).toBe("1");
    await userEvent.click(housingButton);
    expect(screen.getByRole("checkbox", { name: /Housing Prices/ })).toBeChecked();
  });

  it("marks planned layers with a badge", async () => {
    render(<BottomBar layers={LAYERS} active={new Set()} onToggle={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "Transit" }));
    expect(screen.getByText("Planned")).toBeInTheDocument();
  });

  it("renders a region selector and reports changes", async () => {
    const onRegionChange = vi.fn();
    render(
      <BottomBar
        layers={LAYERS}
        active={new Set()}
        onToggle={() => {}}
        regions={REGIONS}
        regionId="gva"
        onRegionChange={onRegionChange}
      />,
    );
    await userEvent.selectOptions(screen.getByLabelText("Region"), "gta");
    expect(onRegionChange).toHaveBeenCalledWith("gta");
  });

  it("lists data sources in a flyout", async () => {
    render(
      <BottomBar
        layers={LAYERS}
        active={new Set()}
        onToggle={() => {}}
        sources={SOURCES}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Data sources" }));
    const link = screen.getByRole("link", { name: "Metro Vancouver Portal" });
    expect(link).toHaveAttribute("href", "https://example.com/data");
  });

  it("selects all layers in a group via the select-all checkbox", async () => {
    const onToggleGroup = vi.fn();
    render(
      <BottomBar
        layers={LAYERS}
        active={new Set()}
        onToggle={() => {}}
        onToggleGroup={onToggleGroup}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Transit" }));
    await userEvent.click(screen.getByRole("checkbox", { name: "Select all" }));
    // Transit group holds the SkyTrain Expansion layer; select-all activates it.
    expect(onToggleGroup).toHaveBeenCalledWith(["skytrain-expansion"], true);
  });

  it("deselects all layers when select-all is already fully checked", async () => {
    const onToggleGroup = vi.fn();
    render(
      <BottomBar
        layers={LAYERS}
        active={new Set(["skytrain-expansion"])}
        onToggle={() => {}}
        onToggleGroup={onToggleGroup}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Transit" }));
    const selectAll = screen.getByRole("checkbox", { name: "Select all" });
    expect(selectAll).toBeChecked();
    await userEvent.click(selectAll);
    expect(onToggleGroup).toHaveBeenCalledWith(["skytrain-expansion"], false);
  });

  it("closes the open flyout on Escape", async () => {
    render(<BottomBar layers={LAYERS} active={new Set()} onToggle={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "Housing" }));
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByText("Housing Prices")).not.toBeInTheDocument();
  });
});
