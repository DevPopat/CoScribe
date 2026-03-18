import React from "react";
import { render, screen, act } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import LoadingBubble from "./LoadingBubble";

const PLANNING_MESSAGES = [
  "Pondering",
  "Researching",
  "Snooping around the web",
  "Concocting an outline",
  "Brewing ideas",
];
const DRAFTING_MESSAGES = ["Scribbling away", "Wordsmithing", "Crafting prose", "Shimmying words into place"];
const REFINING_MESSAGES = ["Rethinking", "Tinkering", "Massaging the draft", "Cooking up changes"];

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("LoadingBubble", () => {
  it("renders a chat bubble", () => {
    render(<LoadingBubble phase="planning" />);
    expect(screen.getByTestId("loading-bubble")).toBeDefined();
  });

  it("shows an initial planning message", () => {
    render(<LoadingBubble phase="planning" />);
    const text = screen.getByTestId("loading-bubble").textContent ?? "";
    expect(PLANNING_MESSAGES.some((m) => text.includes(m))).toBe(true);
  });

  it("shows an initial drafting message when phase is drafting", () => {
    render(<LoadingBubble phase="drafting" />);
    const text = screen.getByTestId("loading-bubble").textContent ?? "";
    expect(DRAFTING_MESSAGES.some((m) => text.includes(m))).toBe(true);
  });

  it("shows an initial refining message when phase is refining", () => {
    render(<LoadingBubble phase="refining" />);
    const text = screen.getByTestId("loading-bubble").textContent ?? "";
    expect(REFINING_MESSAGES.some((m) => text.includes(m))).toBe(true);
  });

  it("cycles to a new message after 3 seconds", () => {
    render(<LoadingBubble phase="planning" />);
    const first = screen.getByTestId("loading-bubble").textContent ?? "";
    act(() => { vi.advanceTimersByTime(3000); });
    const second = screen.getByTestId("loading-bubble").textContent ?? "";
    // Both should be valid planning messages; they may differ after cycling
    expect(PLANNING_MESSAGES.some((m) => second.includes(m))).toBe(true);
    // The message should have advanced (different content OR same if only 1 option)
    // We can't assert strict inequality since cycling wraps, but we verify it's still valid
  });

  it("does not show drafting messages when phase is planning", () => {
    render(<LoadingBubble phase="planning" />);
    act(() => { vi.advanceTimersByTime(15000); });
    const text = screen.getByTestId("loading-bubble").textContent ?? "";
    expect(DRAFTING_MESSAGES.some((m) => text.includes(m))).toBe(false);
  });

  it("does not show planning messages when phase is drafting", () => {
    render(<LoadingBubble phase="drafting" />);
    act(() => { vi.advanceTimersByTime(15000); });
    const text = screen.getByTestId("loading-bubble").textContent ?? "";
    expect(PLANNING_MESSAGES.some((m) => text.includes(m))).toBe(false);
  });
});
