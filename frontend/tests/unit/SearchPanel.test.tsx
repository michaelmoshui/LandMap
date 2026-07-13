import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

afterEach(() => {
  vi.clearAllMocks();
});

describe("SearchPanel", () => {
  it("searches as the user types and lists results with kind badges", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([KITSILANO]);
    render(<SearchPanel selections={[]} onSelect={() => {}} onRemove={() => {}} />);

    await userEvent.type(screen.getByLabelText("Search boundaries"), "kits");
    expect(await screen.findByText("Kitsilano")).toBeInTheDocument();
    expect(screen.getByText("Neighborhood")).toBeInTheDocument();
    expect(vi.mocked(searchBoundaries)).toHaveBeenCalledWith("kits");
  });

  it("calls onSelect with the clicked result", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([KITSILANO]);
    const onSelect = vi.fn();
    render(<SearchPanel selections={[]} onSelect={onSelect} onRemove={() => {}} />);

    await userEvent.type(screen.getByLabelText("Search boundaries"), "kits");
    await userEvent.click(await screen.findByText("Kitsilano"));
    expect(onSelect).toHaveBeenCalledWith(KITSILANO);
  });

  it("disables results that are already selected", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([KITSILANO]);
    render(<SearchPanel selections={[SELECTED]} onSelect={() => {}} onRemove={() => {}} />);

    await userEvent.type(screen.getByLabelText("Search boundaries"), "kits");
    expect(await screen.findByTestId("search-result")).toBeDisabled();
  });

  it("lists selections with their color swatch and removes on demand", async () => {
    const onRemove = vi.fn();
    render(<SearchPanel selections={[SELECTED]} onSelect={() => {}} onRemove={onRemove} />);

    const item = screen.getByTestId("selected-boundary");
    expect(item).toHaveTextContent("Kitsilano");
    const swatch = item.querySelector(".swatch") as HTMLElement;
    expect(swatch.style.backgroundColor).toBe("rgb(230, 25, 75)");

    await userEvent.click(screen.getByRole("button", { name: "Remove Kitsilano" }));
    expect(onRemove).toHaveBeenCalledWith("hood-kitsilano");
  });

  it("shows an empty state when nothing matches", async () => {
    vi.mocked(searchBoundaries).mockResolvedValue([]);
    render(<SearchPanel selections={[]} onSelect={() => {}} onRemove={() => {}} />);

    await userEvent.type(screen.getByLabelText("Search boundaries"), "zzz");
    expect(await screen.findByText("No matches")).toBeInTheDocument();
  });
});
