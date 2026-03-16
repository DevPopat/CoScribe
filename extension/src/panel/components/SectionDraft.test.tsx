import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import SectionDraft from "./SectionDraft";
import type { Section, EditorStatus } from "../../types";

const editorDetected: EditorStatus = { detected: true, tier: "rich", element: "div[contenteditable]" };
const noEditor: EditorStatus = { detected: false, tier: "none", element: null };

const sectionNoDraft: Section = {
  title: "Intro",
  key_points: ["Why bake?", "What you need"],
  sources: [],
  draft: null,
  approved: false,
};

const sectionWithDraft: Section = {
  ...sectionNoDraft,
  draft: "Baking bread is a joy.",
};

describe("SectionDraft", () => {
  it("renders key points", () => {
    render(
      <SectionDraft
        section={sectionNoDraft} sectionIndex={0} editorStatus={noEditor}
        isLoading={false} onDraft={() => {}} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    expect(screen.getByText("Why bake?")).toBeDefined();
    expect(screen.getByText("What you need")).toBeDefined();
  });

  it('shows "Draft" button when no draft exists', () => {
    render(
      <SectionDraft
        section={sectionNoDraft} sectionIndex={0} editorStatus={noEditor}
        isLoading={false} onDraft={() => {}} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: "Draft" })).toBeDefined();
  });

  it('shows "Regenerate" button when draft exists', () => {
    render(
      <SectionDraft
        section={sectionWithDraft} sectionIndex={0} editorStatus={noEditor}
        isLoading={false} onDraft={() => {}} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: "Regenerate" })).toBeDefined();
  });

  it("calls onDraft when Draft button is clicked", async () => {
    const onDraft = vi.fn();
    const user = userEvent.setup();
    render(
      <SectionDraft
        section={sectionNoDraft} sectionIndex={2} editorStatus={noEditor}
        isLoading={false} onDraft={onDraft} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Draft" }));
    expect(onDraft).toHaveBeenCalledWith(2);
  });

  it("shows Approve button when draft exists and not approved", () => {
    render(
      <SectionDraft
        section={sectionWithDraft} sectionIndex={0} editorStatus={noEditor}
        isLoading={false} onDraft={() => {}} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: "Approve" })).toBeDefined();
  });

  it("disables Insert when no editor detected", () => {
    render(
      <SectionDraft
        section={sectionWithDraft} sectionIndex={0} editorStatus={noEditor}
        isLoading={false} onDraft={() => {}} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    const insert = screen.getByRole("button", { name: "Insert" });
    expect(insert).toHaveProperty("disabled", true);
  });

  it("enables Insert when editor detected and draft exists", () => {
    render(
      <SectionDraft
        section={sectionWithDraft} sectionIndex={0} editorStatus={editorDetected}
        isLoading={false} onDraft={() => {}} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    const insert = screen.getByRole("button", { name: "Insert" });
    expect(insert).toHaveProperty("disabled", false);
  });

  it("displays draft text when available", () => {
    render(
      <SectionDraft
        section={sectionWithDraft} sectionIndex={0} editorStatus={noEditor}
        isLoading={false} onDraft={() => {}} onApprove={() => {}} onInsert={() => {}}
      />,
    );
    expect(screen.getByTestId("draft-text").textContent).toBe("Baking bread is a joy.");
  });
});
