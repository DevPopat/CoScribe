// Ordered adapter registry — first match wins.
// Tier 1 (native API) is checked before Tier 2 (clipboard sim) before Tier 3 (fallback).

import type { EditorAdapter } from "./base";
import { tinymce, ckeditor4, ckeditor5, quill } from "./tier1";
import { tiptap, slate, draftjs, notion } from "./tier2";
import { textarea, contenteditable } from "./tier3";

const adapters: EditorAdapter[] = [
  // Tier 1 — native API
  tinymce,
  ckeditor4,
  ckeditor5,
  quill,
  // Tier 2 — clipboard simulation
  tiptap,
  slate,
  draftjs,
  notion,
  // Tier 3 — fallback
  textarea,
  contenteditable,
];

/** Return the first adapter whose detect() returns true, or null. */
export function detectEditor(): EditorAdapter | null {
  for (const adapter of adapters) {
    if (adapter.detect()) return adapter;
  }
  return null;
}
