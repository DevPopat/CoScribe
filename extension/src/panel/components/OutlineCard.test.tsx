import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import OutlineCard from "./OutlineCard";
import type { Outline } from "../../types";

const outline: Outline = {
  title: "How to Bake Bread",
  brief: "A beginner guide to baking.",
  tone_guidance: "Friendly",
  sections: [
    {
      title: "Introduction",
      key_points: ["Why bake?", "What you need"],
      sources: ["https://baking.com/intro"],
      draft: null,
      approved: false,
    },
    {
      title: "The Process",
      key_points: ["Mixing", "Proofing"],
      sources: [],
      draft: null,
      approved: false,
    },
  ],
};

describe("OutlineCard", () => {
  it("renders the outline title and brief", () => {
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    expect(screen.getByText("How to Bake Bread")).toBeDefined();
    expect(screen.getByText("A beginner guide to baking.")).toBeDefined();
  });

  it("renders a row for each section", () => {
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    expect(screen.getByText("Introduction")).toBeDefined();
    expect(screen.getByText("The Process")).toBeDefined();
  });

  it("key points are not visible when section is collapsed", () => {
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    expect(screen.queryByText("Why bake?")).toBeNull();
    expect(screen.queryByText("Mixing")).toBeNull();
  });

  it("expanding a section reveals its key points", async () => {
    const user = userEvent.setup();
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    await user.click(screen.getByTestId("toggle-section-0"));
    expect(screen.getByText("Why bake?")).toBeDefined();
    expect(screen.getByText("What you need")).toBeDefined();
  });

  it("collapsing an expanded section hides key points", async () => {
    const user = userEvent.setup();
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    await user.click(screen.getByTestId("toggle-section-0"));
    await user.click(screen.getByTestId("toggle-section-0"));
    expect(screen.queryByText("Why bake?")).toBeNull();
  });

  it("shows a Draft button for each section", () => {
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    expect(screen.getAllByRole("button", { name: "Draft" })).toHaveLength(2);
  });

  it("calls onDraft with the correct index", async () => {
    const onDraft = vi.fn();
    const user = userEvent.setup();
    render(<OutlineCard outline={outline} onDraft={onDraft} />);
    const draftButtons = screen.getAllByRole("button", { name: "Draft" });
    await user.click(draftButtons[1]);
    expect(onDraft).toHaveBeenCalledWith(1);
  });

  it("shows Sources accordion when section has sources and is expanded", async () => {
    const user = userEvent.setup();
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    await user.click(screen.getByTestId("toggle-section-0"));
    expect(screen.getByText("Sources (1)")).toBeDefined();
  });

  it("source URLs are hidden until Sources accordion is opened", async () => {
    const user = userEvent.setup();
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    await user.click(screen.getByTestId("toggle-section-0"));
    expect(screen.queryByText("https://baking.com/intro")).toBeNull();
    await user.click(screen.getByText("Sources (1)"));
    expect(screen.getByText("https://baking.com/intro")).toBeDefined();
  });

  it("does not show Sources accordion for sections with no sources", async () => {
    const user = userEvent.setup();
    render(<OutlineCard outline={outline} onDraft={() => {}} />);
    await user.click(screen.getByTestId("toggle-section-1"));
    expect(screen.queryByText(/Sources/)).toBeNull();
  });
});
