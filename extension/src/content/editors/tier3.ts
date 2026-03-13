// Tier 3: Fallback adapters for plain textareas and contenteditable elements.

import type { EditorAdapter } from "./base";

/** Textarea or input[type=text] — inserts at cursor via selectionStart/selectionEnd. */
export const textarea: EditorAdapter = {
  name: "textarea",
  tier: "plain",
  detect() {
    return !!document.querySelector("textarea, input[type=text]");
  },
  insert(text: string) {
    const el = document.querySelector("textarea, input[type=text]") as
      | HTMLTextAreaElement
      | HTMLInputElement
      | null;
    if (!el) return;
    el.focus();
    const start = el.selectionStart ?? el.value.length;
    const end = el.selectionEnd ?? el.value.length;
    el.setRangeText(text, start, end, "end");
    el.dispatchEvent(new Event("input", { bubbles: true }));
  },
};

/** Generic contenteditable element. */
export const contenteditable: EditorAdapter = {
  name: "contenteditable",
  tier: "plain",
  detect() {
    return !!document.querySelector("[contenteditable=true]");
  },
  insert(text: string) {
    const el = document.querySelector("[contenteditable=true]") as HTMLElement | null;
    if (!el) return;
    el.focus();
    document.execCommand("insertText", false, text);
  },
};
