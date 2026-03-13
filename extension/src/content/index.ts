// Content script injected into web pages.
// Handles DETECT_EDITOR (returns EditorStatus) and INSERT_TEXT messages
// from the panel/background service worker.

import type { EditorStatus } from "../types";
import { detectEditor } from "./editors/registry";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "DETECT_EDITOR") {
    const adapter = detectEditor();
    const status: EditorStatus = adapter
      ? { detected: true, tier: adapter.tier, element: adapter.name }
      : { detected: false, tier: "none", element: null };
    sendResponse(status);
  } else if (message.type === "INSERT_TEXT") {
    const adapter = detectEditor();
    if (adapter && typeof message.text === "string") {
      adapter.insert(message.text);
      sendResponse({ ok: true });
    } else {
      sendResponse({ ok: false, error: "No editor detected" });
    }
  } else if (message.type === "PING") {
    sendResponse({ ok: true });
  }
  return undefined;
});
