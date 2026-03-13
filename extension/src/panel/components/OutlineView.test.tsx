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

describe("OutlineView", () => {
  it("renders the outline title and brief", () => {
    render(
      <OutlineView outline={outline} currentSectionIndex={0} onSelectSection={() => {}} />,
    );
    expect(screen.getByText("How to Bake Bread")).toBeDefined();
    expect(screen.getByText("A beginner guide.")).toBeDefined();
  });

  it("shows checkmark for approved sections", () => {
    render(
      <OutlineView outline={outline} currentSectionIndex={0} onSelectSection={() => {}} />,
    );
    const item0 = screen.getByTestId("section-item-0");
    const item1 = screen.getByTestId("section-item-1");
    expect(item0.textContent).toContain("\u25CB");
    expect(item1.textContent).toContain("\u2713");
  });

  it("highlights the current section with bold", () => {
    render(
      <OutlineView outline={outline} currentSectionIndex={0} onSelectSection={() => {}} />,
    );
    const item0 = screen.getByTestId("section-item-0");
    expect(item0.style.fontWeight).toBe("bold");
  });

  it("calls onSelectSection when a section is clicked", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(
      <OutlineView outline={outline} currentSectionIndex={0} onSelectSection={onSelect} />,
    );
    await user.click(screen.getByText(/Process/));
    expect(onSelect).toHaveBeenCalledWith(1);
  });
});
