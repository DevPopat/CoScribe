import { renderHook, act } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import useSession from "./useSession";
import api from "./useAPI";
import type { Outline, WritingSession } from "../../types";

vi.mock("./useAPI", () => ({
  default: {
    createSession: vi.fn(),
    getSession: vi.fn(),
    generatePlan: vi.fn(),
    draftSection: vi.fn(),
    approveSection: vi.fn(),
    refinePlan: vi.fn(),
  },
}));

const mockSession: WritingSession = {
  id: "sess-1",
  topic: "Baking bread",
  audience: "Beginners",
  notes: "",
  writing_samples: [],
  reference_urls: [],
  status: "pending",
  outline: null,
  refinement_history: [],
};

const mockOutline: Outline = {
  title: "How to Bake Bread",
  brief: "A beginner guide.",
  tone_guidance: "Friendly",
  sections: [
    { title: "Intro", key_points: ["Why bake?"], draft: null, approved: false },
    { title: "Process", key_points: ["Mixing"], draft: null, approved: false },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("useSession", () => {
  it("initializes with null session and no loading", () => {
    const { result } = renderHook(() => useSession());
    expect(result.current.session).toBeNull();
    expect(result.current.outline).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("startSession creates session and generates plan", async () => {
    vi.mocked(api.createSession).mockResolvedValue(mockSession);
    vi.mocked(api.generatePlan).mockResolvedValue(mockOutline);

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.startSession({
        topic: "Baking bread",
        audience: "Beginners",
      });
    });

    expect(api.createSession).toHaveBeenCalledWith({
      topic: "Baking bread",
      audience: "Beginners",
    });
    expect(api.generatePlan).toHaveBeenCalledWith("sess-1");
    expect(result.current.session?.status).toBe("outline_ready");
    expect(result.current.outline?.title).toBe("How to Bake Bread");
    expect(result.current.isLoading).toBe(false);
  });

  it("startSession sets error on failure", async () => {
    vi.mocked(api.createSession).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.startSession({
        topic: "Test",
        audience: "All",
      });
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.session).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("draftSection stores draft and sets status to drafting", async () => {
    vi.mocked(api.createSession).mockResolvedValue(mockSession);
    vi.mocked(api.generatePlan).mockResolvedValue(mockOutline);
    vi.mocked(api.draftSection).mockResolvedValue({ draft: "Draft text." });

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.startSession({
        topic: "Baking bread",
        audience: "Beginners",
      });
    });

    await act(async () => {
      await result.current.draftSection(0);
    });

    expect(api.draftSection).toHaveBeenCalledWith("sess-1", 0);
    expect(result.current.outline?.sections[0].draft).toBe("Draft text.");
    expect(result.current.session?.status).toBe("drafting");
    expect(result.current.currentSectionIndex).toBe(0);
  });

  it("approveSection marks section approved", async () => {
    vi.mocked(api.createSession).mockResolvedValue(mockSession);
    vi.mocked(api.generatePlan).mockResolvedValue(mockOutline);
    vi.mocked(api.draftSection).mockResolvedValue({ draft: "Draft text." });
    vi.mocked(api.approveSection).mockResolvedValue({
      approved: true,
      section_index: 0,
    });

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.startSession({
        topic: "Baking bread",
        audience: "Beginners",
      });
    });

    await act(async () => {
      await result.current.draftSection(0);
    });

    await act(async () => {
      await result.current.approveSection(0);
    });

    expect(result.current.outline?.sections[0].approved).toBe(true);
  });

  it("approveSection with edited text replaces draft", async () => {
    vi.mocked(api.createSession).mockResolvedValue(mockSession);
    vi.mocked(api.generatePlan).mockResolvedValue(mockOutline);
    vi.mocked(api.approveSection).mockResolvedValue({
      approved: true,
      section_index: 0,
    });

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.startSession({
        topic: "Baking bread",
        audience: "Beginners",
      });
    });

    await act(async () => {
      await result.current.approveSection(0, "My edited text.");
    });

    expect(api.approveSection).toHaveBeenCalledWith(
      "sess-1",
      0,
      "My edited text.",
    );
    expect(result.current.outline?.sections[0].draft).toBe("My edited text.");
    expect(result.current.outline?.sections[0].approved).toBe(true);
  });

  it("approving all sections sets status to complete", async () => {
    vi.mocked(api.createSession).mockResolvedValue(mockSession);
    vi.mocked(api.generatePlan).mockResolvedValue(mockOutline);
    vi.mocked(api.approveSection).mockResolvedValue({
      approved: true,
      section_index: 0,
    });

    const { result } = renderHook(() => useSession());

    await act(async () => {
      await result.current.startSession({
        topic: "Baking bread",
        audience: "Beginners",
      });
    });

    await act(async () => {
      await result.current.approveSection(0, "Text 1");
    });

    await act(async () => {
      await result.current.approveSection(1, "Text 2");
    });

    expect(result.current.session?.status).toBe("complete");
  });
});
