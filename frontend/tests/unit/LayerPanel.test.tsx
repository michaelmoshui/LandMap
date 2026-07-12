import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { LayerMeta } from "../../src/api/types";
import LayerPanel, { groupByCategory } from "../../src/components/LayerPanel";

const LAYERS: LayerMeta[] = [
  { id: "housing-prices", title: "Housing Prices", description: "", category: "baseline" },
  { id: "skytrain-expansion", title: "SkyTrain Expansion", description: "", category: "planned" },
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
});
