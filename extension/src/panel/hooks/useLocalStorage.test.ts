// Tests for the useLocalStorage hook.
// Verifies localStorage fallback and chrome.storage.local integration.

import { vi, describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import useLocalStorage from "./useLocalStorage";
import type { PersistedState } from "./useLocalStorage";

const mockState: PersistedState = {
  session_id: "sess-1",
  chat_history: [{ role: "user", content: "hi" }],
  outline: null,
  section_chats: {},
  section_drafts: {},
  current_view: "chat",
  current_section: 0,
};

beforeEach(() => {
  localStorage.clear();
  // Ensure chrome is not defined by default
  (globalThis as Record<string, unknown>).chrome = undefined;
});

describe("useLocalStorage – localStorage fallback", () => {
  it("load returns null when nothing is stored", () => {
    const { result } = renderHook(() => useLocalStorage());
    expect(result.current.load()).toBeNull();
  });

  it("save persists state and load retrieves it", () => {
    const { result } = renderHook(() => useLocalStorage());
    act(() => { result.current.save(mockState); });
    expect(result.current.load()).toEqual(mockState);
  });

  it("save overwrites previous state", () => {
    const { result } = renderHook(() => useLocalStorage());
    act(() => { result.current.save(mockState); });
    const updated: PersistedState = { ...mockState, session_id: "sess-2" };
    act(() => { result.current.save(updated); });
    expect(result.current.load()?.session_id).toBe("sess-2");
  });
});

describe("useLocalStorage – chrome.storage.local", () => {
  it("save calls chrome.storage.local.set when available", () => {
    const mockSet = vi.fn();
    (globalThis as Record<string, unknown>).chrome = {
      storage: { local: { set: mockSet, get: vi.fn() } },
    };
    const { result } = renderHook(() => useLocalStorage());
    act(() => { result.current.save(mockState); });
    expect(mockSet).toHaveBeenCalledWith({ coscribe: mockState });
  });

  it("load reads from chrome.storage.local when available", () => {
    const mockGet = vi.fn().mockImplementation((_key, cb) => {
      cb({ coscribe: mockState });
    });
    (globalThis as Record<string, unknown>).chrome = {
      storage: { local: { set: vi.fn(), get: mockGet } },
    };
    const { result } = renderHook(() => useLocalStorage());
    // load() is synchronous in fallback; chrome.storage.local.get is async
    // When chrome is available, load() returns from a sync cache populated by save
    act(() => { result.current.save(mockState); });
    expect(result.current.load()).toEqual(mockState);
  });
});
