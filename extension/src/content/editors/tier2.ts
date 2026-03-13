// Tier 2: Clipboard-simulation adapters for editors without a public JS API.
// Inserts text by focusing the element, writing to clipboard, and executing paste.

import type { EditorAdapter } from "./base";

function clipboardInsert(el: HTMLElement, text: string): void {
  el.focus();
  const dt = new DataTransfer();
  dt.setData("text/plain", text);
  const event = new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true });
  el.dispatchEvent(event);
}

function makeClipboardAdapter(name: string, selector: string): EditorAdapter {
  return {
    name,
    tier: "plain",
    detect() {
      return !!document.querySelector(selector);
    },
    insert(text: string) {
      const el = document.querySelector(selector) as HTMLElement | null;
      if (el) clipboardInsert(el, text);
    },
  };
}

/** Tiptap (ProseMirror-based) */
export const tiptap = makeClipboardAdapter("Tiptap", ".ProseMirror");

/** Slate.js */
export const slate = makeClipboardAdapter("Slate", "[data-slate-editor]");

/** Draft.js (Facebook) */
export const draftjs = makeClipboardAdapter("Draft.js", ".DraftEditor-root");

/** Notion — page body editor */
export const notion = makeClipboardAdapter("Notion", ".notion-page-content");
