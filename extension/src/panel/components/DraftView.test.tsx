import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import DraftView from "./DraftView";
import type { Outline, EditorStatus } from "../../types";

const outline: Outline = {
  title: "How to Bake Bread",
  brief: "A beginner guide.",
  tone_guidance: "Friendly",
  sections: [
    {
      title: "Introduction",
      key_points: ["Why bake?", "What you need"],
      sources: ["https://baking.com"],
      draft: "Baking is a joy.",
      approved: false,
    },
    {
      title: "The Process",
      key_points: ["Mixing"],
      sources: [],
      draft: null,
      approved: false,
    },
  ],
};

const editorDetected: EditorStatus = { detected: true, tier: "rich", element: "div" };
const noEditor: EditorStatus = { detected: false, tier: "none", element: null };

function renderDraftView(overrides: Partial<Parameters<typeof DraftView>[0]> = {}) {
  const defaults = {
    outline,
    currentSectionIndex: 0,
    sectionChats: {},
    editorStatus: noEditor,
    isLoading: false,
    error: null,
    onBack: vi.fn(),
    onSelectSection: vi.fn(),
    onSave: vi.fn(),
    onInsert: vi.fn(),
    onRefineDraft: vi.fn(),
  };
  return render(<DraftView {...defaults} {...overrides} />);
}

describe("DraftView", () => {
  it("renders the current section title", () => {
    renderDraftView();
    expect(screen.getByRole("heading", { name: "Introduction" })).toBeDefined();
  });

  it("renders SectionNav with section pills", () => {
    renderDraftView();
    // SectionNav renders a button per section
    const nav = screen.getByRole("navigation");
    expect(nav).toBeDefined();
  });

  it("shows key points for the current section", () => {
    renderDraftView();
    expect(screen.getByText("Why bake?")).toBeDefined();
    expect(screen.getByText("What you need")).toBeDefined();
  });

  it("shows Sources accordion when section has sources", () => {
    renderDraftView();
    expect(screen.getByText(/Sources \(1\)/)).toBeDefined();
  });

  it("sources are hidden until accordion is opened", async () => {
    const user = userEvent.setup();
    renderDraftView();
    expect(screen.queryByText("https://baking.com")).toBeNull();
    await user.click(screen.getByText(/Sources \(1\)/));
    expect(screen.getByText("https://baking.com")).toBeDefined();
  });

  it("renders a textarea with the current draft", () => {
    renderDraftView();
    const textarea = screen.getByRole("textbox", { name: /draft/i });
    expect((textarea as HTMLTextAreaElement).value).toBe("Baking is a joy.");
  });

  it("back button calls onBack", async () => {
    const onBack = vi.fn();
    const user = userEvent.setup();
    renderDraftView({ onBack });
    await user.click(screen.getByRole("button", { name: /back/i }));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("save button calls onSave with section index and current textarea content", async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();
    renderDraftView({ onSave });
    const textarea = screen.getByRole("textbox", { name: /draft/i });
    await user.clear(textarea);
    await user.type(textarea, "Edited draft.");
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(onSave).toHaveBeenCalledWith(0, "Edited draft.");
  });

  it("insert button calls onInsert with draft text when editor detected", async () => {
    const onInsert = vi.fn();
    const user = userEvent.setup();
    renderDraftView({ onInsert, editorStatus: editorDetected });
    await user.click(screen.getByRole("button", { name: /insert/i }));
    expect(onInsert).toHaveBeenCalledWith("Baking is a joy.");
  });

  it("insert button is disabled when no editor detected", () => {
    renderDraftView({ editorStatus: noEditor });
    expect(screen.getByRole("button", { name: /insert/i })).toHaveProperty("disabled", true);
  });

  it("shows error message when error prop is set", () => {
    renderDraftView({ error: "Something went wrong." });
    expect(screen.getByText("Something went wrong.")).toBeDefined();
  });

  it("renders per-section chat messages", () => {
    renderDraftView({
      sectionChats: {
        0: [
          { role: "user", content: "Make it shorter." },
          { role: "assistant", content: "Done!" },
        ],
      },
    });
    expect(screen.getByText("Make it shorter.")).toBeDefined();
    expect(screen.getByText("Done!")).toBeDefined();
  });

  it("section chat input calls onRefineDraft when submitted", async () => {
    const onRefineDraft = vi.fn();
    const user = userEvent.setup();
    renderDraftView({ onRefineDraft });
    await user.type(screen.getByRole("textbox", { name: /refine/i }), "Be more vivid");
    await user.click(screen.getByRole("button", { name: /refine/i }));
    expect(onRefineDraft).toHaveBeenCalledWith(0, "Be more vivid");
  });
});
