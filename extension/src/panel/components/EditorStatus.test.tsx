import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import EditorStatus from "./EditorStatus";

describe("EditorStatus", () => {
  it("shows green dot and element name when editor detected (rich)", () => {
    render(
      <EditorStatus status={{ detected: true, tier: "rich", element: "div[contenteditable]" }} />,
    );
    const dot = screen.getByTestId("editor-status-dot");
    expect(dot.style.backgroundColor).toBe("green");
    expect(screen.getByTestId("editor-status-label").textContent).toBe(
      "div[contenteditable] (rich)",
    );
  });

  it("shows orange dot for plain tier", () => {
    render(
      <EditorStatus status={{ detected: true, tier: "plain", element: "textarea" }} />,
    );
    const dot = screen.getByTestId("editor-status-dot");
    expect(dot.style.backgroundColor).toBe("orange");
    expect(screen.getByTestId("editor-status-label").textContent).toBe("textarea (plain)");
  });

  it("shows red dot and fallback label when no editor detected", () => {
    render(
      <EditorStatus status={{ detected: false, tier: "none", element: null }} />,
    );
    const dot = screen.getByTestId("editor-status-dot");
    expect(dot.style.backgroundColor).toBe("red");
    expect(screen.getByTestId("editor-status-label").textContent).toBe("No editor detected");
  });
});
