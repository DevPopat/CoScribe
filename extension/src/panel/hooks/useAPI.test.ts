// Tests for the useAPI typed HTTP client.
// Mocks globalThis.fetch to verify correct URLs and request bodies.

import { vi, describe, it, expect, beforeEach } from "vitest";
import api from "./useAPI";
import type { ChatResponse, SectionRefineResponse } from "../../types";

function mockFetch(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("api.chatIntake", () => {
  it("POSTs to /sessions/chat with messages array", async () => {
    const response: ChatResponse = {
      reply: "Got it! What's your target audience?",
      ready: false,
    };
    globalThis.fetch = mockFetch(response);

    await api.chatIntake([{ role: "user", content: "I want to write about ML." }]);

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/sessions/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          messages: [{ role: "user", content: "I want to write about ML." }],
        }),
      }),
    );
  });

  it("returns ChatResponse from server", async () => {
    const response: ChatResponse = {
      reply: "All set!",
      ready: true,
      extracted: { topic: "ML", audience: "Students" },
    };
    globalThis.fetch = mockFetch(response);

    const result = await api.chatIntake([{ role: "user", content: "hi" }]);

    expect(result.reply).toBe("All set!");
    expect(result.ready).toBe(true);
    expect(result.extracted?.topic).toBe("ML");
  });
});

describe("api.refineSectionDraft", () => {
  it("POSTs to the correct section refine URL", async () => {
    const response: SectionRefineResponse = {
      draft: "Refined text.",
      reply: "Tightened it up.",
    };
    globalThis.fetch = mockFetch(response);

    await api.refineSectionDraft("sess-1", 2, "Make it shorter", "Original text.");

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/sessions/sess-1/sections/2/refine",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("sends message and current_draft in request body", async () => {
    const response: SectionRefineResponse = { draft: "d", reply: "r" };
    globalThis.fetch = mockFetch(response);

    await api.refineSectionDraft("sess-1", 0, "Be vivid", "Plain text.");

    const body = JSON.parse(
      (fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body,
    );
    expect(body.message).toBe("Be vivid");
    expect(body.current_draft).toBe("Plain text.");
  });

  it("returns SectionRefineResponse from server", async () => {
    const response: SectionRefineResponse = {
      draft: "New draft.",
      key_points: ["Point A"],
      sources: ["https://example.com"],
      reply: "Added a source.",
    };
    globalThis.fetch = mockFetch(response);

    const result = await api.refineSectionDraft("sess-1", 0, "msg", "draft");

    expect(result.draft).toBe("New draft.");
    expect(result.key_points).toEqual(["Point A"]);
    expect(result.sources).toEqual(["https://example.com"]);
    expect(result.reply).toBe("Added a source.");
  });
});
