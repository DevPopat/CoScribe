import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import OutlineView from "./OutlineView";
import type { Outline } from "../../types";

const outline: Outline = {
  title: "How to Bake Bread",
  brief: "A beginner guide.",
  tone_guidance: "Friendly",
  sections: [
    { title: "Intro", key_points: ["Why bake?"], draft: null, approved: false },
    { title: "Process", key_points: ["Mixing"], draft: "Draft.", approved: true },
  ],
};

const defaultProps = {
  outline,
  currentSectionIndex: 0,
  onSelectSection: () => {},
  refinementHistory: [],
  isRefining: false,
  outlineChanged: false,
  onRefine: () => {},
  onOutlineTabClick: () => {},
};

describe("OutlineView", () => {
  it("renders the outline title and brief", () => {
    render(<OutlineView {...defaultProps} />);
    expect(screen.getByText("How to Bake Bread")).toBeDefined();
    expect(screen.getByText("A beginner guide.")).toBeDefined();
  });

  it("shows checkmark for approved sections", () => {
    render(<OutlineView {...defaultProps} />);
    const item0 = screen.getByTestId("section-item-0");
    const item1 = screen.getByTestId("section-item-1");
    expect(item0.textContent).toContain("\u25CB");
    expect(item1.textContent).toContain("\u2713");
  });

  it("highlights the current section with bold", () => {
    render(<OutlineView {...defaultProps} />);
    const item0 = screen.getByTestId("section-item-0");
    expect(item0.style.fontWeight).toBe("bold");
  });

  it("calls onSelectSection when a section is clicked", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<OutlineView {...defaultProps} onSelectSection={onSelect} />);
    await user.click(screen.getByText(/Process/));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("shows Outline and Refine tabs", () => {
    render(<OutlineView {...defaultProps} />);
    expect(screen.getByTestId("tab-outline")).toBeDefined();
    expect(screen.getByTestId("tab-refine")).toBeDefined();
  });

  it("switches to Refine tab and shows chat", async () => {
    const user = userEvent.setup();
    render(<OutlineView {...defaultProps} />);
    await user.click(screen.getByTestId("tab-refine"));
    expect(screen.getByTestId("refine-chat")).toBeDefined();
  });

  it("shows badge on Outline tab when outline changed and on Refine tab", async () => {
    const user = userEvent.setup();
    render(<OutlineView {...defaultProps} outlineChanged={true} />);
    // Switch to refine tab so badge is visible
    await user.click(screen.getByTestId("tab-refine"));
    expect(screen.getByTestId("tab-outline").textContent).toContain("\u2022");
  });

  it("clears badge when Outline tab is clicked", async () => {
    const onOutlineTabClick = vi.fn();
    const user = userEvent.setup();
    render(
      <OutlineView {...defaultProps} outlineChanged={true} onOutlineTabClick={onOutlineTabClick} />,
    );
    await user.click(screen.getByTestId("tab-refine"));
    await user.click(screen.getByTestId("tab-outline"));
    expect(onOutlineTabClick).toHaveBeenCalled();
  });
});
