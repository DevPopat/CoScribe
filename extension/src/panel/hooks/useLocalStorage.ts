// Persistence hook for CoScribe panel state.
// Uses chrome.storage.local in extension context; falls back to localStorage
// for dev/test environments where chrome is not available.

import type { Outline } from "../../types";

export interface PersistedState {
  session_id: string | null;
  chat_history: { role: "user" | "assistant"; content: string }[];
  outline: Outline | null;
  section_chats: Record<number, { role: "user" | "assistant"; content: string }[]>;
  section_drafts: Record<number, string>;
  current_view: string;
  current_section: number;
}

const STORAGE_KEY = "coscribe";

function hasChromeStorage(): boolean {
  return (
    typeof chrome !== "undefined" &&
    chrome?.storage?.local != null
  );
}

export default function useLocalStorage() {
  // In-memory cache so load() stays synchronous even when chrome.storage is used.
  // save() populates the cache; chrome.storage.local.set persists it asynchronously.
  let cache: PersistedState | null = null;

  function save(state: PersistedState): void {
    cache = state;
    if (hasChromeStorage()) {
      chrome.storage.local.set({ [STORAGE_KEY]: state });
    } else {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }
  }

  function load(): PersistedState | null {
    if (cache !== null) return cache;
    if (hasChromeStorage()) {
      // Kick off async hydration for next render; return null on first call
      chrome.storage.local.get(STORAGE_KEY, (result) => {
        cache = (result[STORAGE_KEY] as PersistedState) ?? null;
      });
      return null;
    }
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as PersistedState;
    } catch {
      return null;
    }
  }

  function clear(): void {
    cache = null;
    if (hasChromeStorage()) {
      chrome.storage.local.remove(STORAGE_KEY);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  return { save, load, clear };
}
