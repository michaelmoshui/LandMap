import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentProps } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { BoundarySummary } from "../../src/api/types";
import SearchPanel from "../../src/components/SearchPanel";
import type { SelectedBoundary } from "../../src/map/selection";

vi.mock("../../src/api/client", () => ({
  searchBoundaries: vi.fn(),
}));

import { searchBoundaries } from "../../src/api/client";

const KITSILANO: BoundarySummary = {
  id: "hood-kitsilano",
  name: "Kitsilano",
  kind: "neighborhood",
};

const SELECTED: SelectedBoundary = { ...KITSILANO, color: "#e6194b" };

// Most tests render the panel already open; a couple exercise the toggle.
function renderPanel(props: Partial<ComponentProps<typeof SearchPanel>> = {}) {
  return render(
    <SearchPanel
      selections={[]}
      onSelect={() => {}}
      onRemove={() => {}}
      open
      onOpenChange={() => {}}
      {...props}
    />,
  );
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("SearchPanel", () => {
  it("searches as the user types and lists results with kind badges", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([KITSILANO]);
    renderPanel();

    await userEvent.type(screen.getByLabelText("Search boundaries"), "kits");
    expect(await screen.findByText("Kitsilano")).toBeInTheDocument();
    expect(screen.getByText("Neighborhood")).toBeInTheDocument();
    expect(vi.mocked(searchBoundaries)).toHaveBeenCalledWith("kits");
  });

  it("calls onSelect with the clicked result", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([KITSILANO]);
    const onSelect = vi.fn();
    renderPanel({ onSelect });

    await userEvent.type(screen.getByLabelText("Search boundaries"), "kits");
    await userEvent.click(await screen.findByText("Kitsilano"));
    expect(onSelect).toHaveBeenCalledWith(KITSILANO);
  });

  it("disables results that are already selected", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([KITSILANO]);
    renderPanel({ selections: [SELECTED] });

    await userEvent.type(screen.getByLabelText("Search boundaries"), "kits");
    expect(await screen.findByTestId("search-result")).toBeDisabled();
  });

  it("lists selections and removes on demand", async () => {
    const onRemove = vi.fn();
    renderPanel({ selections: [SELECTED], onRemove });

    const item = screen.getByTestId("selected-boundary");
    expect(item).toHaveTextContent("Kitsilano");

    await userEvent.click(screen.getByRole("button", { name: "Remove Kitsilano" }));
    expect(onRemove).toHaveBeenCalledWith("hood-kitsilano");
  });

  it("shows a color swatch only for lot selections", () => {
    const lot: SelectedBoundary = {
      id: "lot-007-241-374",
      name: "Lot 007-241-374 (2131 W 4th Ave)",
      kind: "lot",
      color: "#3cb44b",
    };
    renderPanel({ selections: [SELECTED, lot] });

    const items = screen.getAllByTestId("selected-boundary");
    expect(items[0].querySelector(".swatch")).toBeNull();
    const swatch = items[1].querySelector(".swatch") as HTMLElement;
    expect(swatch.style.backgroundColor).toBe("rgb(60, 180, 75)");
  });

  it("shows an empty state when nothing matches", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([]);
    renderPanel();

    await userEvent.type(screen.getByLabelText("Search boundaries"), "zzz");
    expect(await screen.findByText("No matches")).toBeInTheDocument();
  });

  it("toggles open/collapsed via the always-visible search icon", async () => {
    const onOpenChange = vi.fn();
    const { rerender } = render(
      <SearchPanel
        selections={[]}
        onSelect={() => {}}
        onRemove={() => {}}
        open={false}
        onOpenChange={onOpenChange}
      />,
    );

    // Collapsed: the input is disabled and out of the tab order; clicking the
    // icon asks to open.
    expect(screen.getByLabelText("Search boundaries")).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Show search" }));
    expect(onOpenChange).toHaveBeenCalledWith(true);

    // Open: the input is enabled and the icon now hides the panel.
    rerender(
      <SearchPanel
        selections={[]}
        onSelect={() => {}}
        onRemove={() => {}}
        open
        onOpenChange={onOpenChange}
      />,
    );
    expect(screen.getByLabelText("Search boundaries")).toBeEnabled();
    await userEvent.click(screen.getByRole("button", { name: "Hide search" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
