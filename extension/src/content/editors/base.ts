// Abstract editor adapter interface.
// Each adapter knows how to detect a specific editor and insert text into it.

import type { EditorTier } from "../../types";

export interface EditorAdapter {
  /** Human-readable name shown in the EditorStatus bar. */
  name: string;
  /** Tier determines insertion strategy: rich = native API, plain = clipboard sim, none = fallback. */
  tier: EditorTier;
  /** Return true if this editor is present on the page. */
  detect(): boolean;
  /** Insert text at the current cursor position (or append). */
  insert(text: string): void;
}
