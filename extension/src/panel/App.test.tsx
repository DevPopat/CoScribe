import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import App from "./App";

// Mock all hooks and child views so tests are isolated to App routing logic
vi.mock("./hooks/useSession", () => ({
  default: vi.fn(),
}));
vi.mock("./hooks/useEditorStatus", () => ({
  default: vi.fn(() => ({ detected: false, tier: "none", element: null })),
}));
vi.mock("./hooks/useLocalStorage", () => ({
  default: () => ({ save: vi.fn(), load: () => null }),
}));
vi.mock("./components/ChatView", () => ({
  default: () => <div data-testid="chat-view-mock" />,
}));
vi.mock("./components/DraftView", () => ({
  default: () => <div data-testid="draft-view-mock" />,
}));

import useSession from "./hooks/useSession";

const baseSession = {
  session: null,
  outline: null,
  currentSectionIndex: 0,
  currentView: "chat" as const,
  isLoading: false,
  error: null,
  chatHistory: [],
  sectionChats: {},
  refinementHistory: [],
  isRefining: false,
  outlineChanged: false,
  sendChatMessage: vi.fn(),
  startSession: vi.fn(),
  draftSection: vi.fn(),
  approveSection: vi.fn(),
  refineOutline: vi.fn(),
  refineSectionDraft: vi.fn(),
  clearOutlineChanged: vi.fn(),
};

beforeEach(() => {
  vi.mocked(useSession).mockReturnValue(baseSession);
  vi.clearAllMocks();
  vi.mocked(useSession).mockReturnValue(baseSession);
});

describe("App", () => {
  it("renders the CoScribe heading", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /coscribe/i })).toBeDefined();
  });

  it("renders the + New Session button", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /new session/i })).toBeDefined();
  });

  it("renders ChatView when currentView is chat", () => {
    vi.mocked(useSession).mockReturnValue({ ...baseSession, currentView: "chat" });
    render(<App />);
    expect(screen.getByTestId("chat-view-mock")).toBeDefined();
    expect(screen.queryByTestId("draft-view-mock")).toBeNull();
  });

  it("renders DraftView when currentView is draft", () => {
    const outline = {
      title: "T", brief: "b", tone_guidance: "n",
      sections: [{ title: "S", key_points: [], sources: [], draft: null, approved: false }],
    };
    vi.mocked(useSession).mockReturnValue({
      ...baseSession,
      currentView: "draft",
      outline,
    });
    render(<App />);
    expect(screen.getByTestId("draft-view-mock")).toBeDefined();
    expect(screen.queryByTestId("chat-view-mock")).toBeNull();
  });

  it("New Session resets to chat view without confirm when no drafts", async () => {
    const confirmSpy = vi.spyOn(window, "confirm");
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: /new session/i }));
    expect(confirmSpy).not.toHaveBeenCalled();
  });

  it("New Session shows confirm when a section has a draft", async () => {
    const outline = {
      title: "T", brief: "b", tone_guidance: "n",
      sections: [{ title: "S", key_points: [], sources: [], draft: "Some draft.", approved: false }],
    };
    vi.mocked(useSession).mockReturnValue({ ...baseSession, outline });
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: /new session/i }));
    expect(window.confirm).toHaveBeenCalled();
  });
});
