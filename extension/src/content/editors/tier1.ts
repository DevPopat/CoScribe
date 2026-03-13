// Tier 1: Native API adapters for editors that expose a JS API on the window.

import type { EditorAdapter } from "./base";

/** TinyMCE — detected via window.tinymce with active editors. */
export const tinymce: EditorAdapter = {
  name: "TinyMCE",
  tier: "rich",
  detect() {
    const t = (window as any).tinymce;
    return !!(t && t.activeEditor);
  },
  insert(text: string) {
    const editor = (window as any).tinymce.activeEditor;
    editor.execCommand("mceInsertContent", false, text);
  },
};

/** CKEditor 4 — detected via window.CKEDITOR with instances. */
export const ckeditor4: EditorAdapter = {
  name: "CKEditor 4",
  tier: "rich",
  detect() {
    const ck = (window as any).CKEDITOR;
    if (!ck?.instances) return false;
    return Object.keys(ck.instances).length > 0;
  },
  insert(text: string) {
    const ck = (window as any).CKEDITOR;
    const name = Object.keys(ck.instances)[0];
    ck.instances[name].insertText(text);
  },
};

/** CKEditor 5 — detected via .ck-editor__editable with ckeditorInstance property. */
export const ckeditor5: EditorAdapter = {
  name: "CKEditor 5",
  tier: "rich",
  detect() {
    const el = document.querySelector(".ck-editor__editable") as any;
    return !!(el && el.ckeditorInstance);
  },
  insert(text: string) {
    const el = document.querySelector(".ck-editor__editable") as any;
    const editor = el.ckeditorInstance;
    editor.model.change((writer: any) => {
      writer.insertText(text, editor.model.document.selection.getFirstPosition());
    });
  },
};

/** Quill — detected via .ql-container element with __quill property. */
export const quill: EditorAdapter = {
  name: "Quill",
  tier: "rich",
  detect() {
    const el = document.querySelector(".ql-container") as any;
    return !!(el && el.__quill);
  },
  insert(text: string) {
    const el = document.querySelector(".ql-container") as any;
    const q = el.__quill;
    const range = q.getSelection(true);
    q.insertText(range?.index ?? q.getLength(), text);
  },
};
