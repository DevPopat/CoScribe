// Section editing view. Shows SectionNav, key points, sources accordion,
// a draft textarea, save/insert actions, and a per-section refinement chat.

import React, { useState } from "react";
import type { Outline, EditorStatus } from "../../types";
import SectionNav from "./SectionNav";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface DraftViewProps {
  outline: Outline;
  currentSectionIndex: number;
  sectionChats: Record<number, Message[]>;
  editorStatus: EditorStatus;
  isLoading: boolean;
  error: string | null;
  onBack: () => void;
  onSelectSection: (index: number) => void;
  onSave: (sectionIndex: number, text: string) => void;
  onInsert: (text: string) => void;
  onRefineDraft: (sectionIndex: number, message: string) => void;
}

export default function DraftView({
  outline,
  currentSectionIndex,
  sectionChats,
  editorStatus,
  isLoading,
  error,
  onBack,
  onSelectSection,
  onSave,
  onInsert,
  onRefineDraft,
}: DraftViewProps) {
  const section = outline.sections[currentSectionIndex];
  const [draftText, setDraftText] = useState(section?.draft ?? "");
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [refineInput, setRefineInput] = useState("");

  const chats = sectionChats[currentSectionIndex] ?? [];

  const handleSend = () => {
    const text = refineInput.trim();
    if (!text) return;
    setRefineInput("");
    onRefineDraft(currentSectionIndex, text);
  };

  return (
    <div className="draft-view" data-testid="draft-view">
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
        <button onClick={onBack} aria-label="Back">← Back</button>
        <h2 style={{ margin: 0 }}>{section.title}</h2>
      </div>

      <SectionNav
        sections={outline.sections}
        currentIndex={currentSectionIndex}
        onSelect={onSelectSection}
      />

      {error && (
        <div className="error-bubble" data-testid="error-bubble" style={{ color: "red", margin: "8px 0" }}>
          {error}
        </div>
      )}

      <div className="key-points" style={{ marginBottom: "8px" }}>
        <strong>Key points</strong>
        <ul>
          {section.key_points.map((kp, i) => <li key={i}>{kp}</li>)}
        </ul>
      </div>

      {section.sources.length > 0 && (
        <div className="sources-accordion" style={{ marginBottom: "8px" }}>
          <button onClick={() => setSourcesOpen((o) => !o)}>
            Sources ({section.sources.length})
          </button>
          {sourcesOpen && (
            <ul>
              {section.sources.map((url, i) => <li key={i}>{url}</li>)}
            </ul>
          )}
        </div>
      )}

      <textarea
        aria-label="Draft"
        value={draftText}
        onChange={(e) => setDraftText(e.target.value)}
        rows={10}
        style={{ width: "100%", marginBottom: "8px" }}
      />

      <div className="draft-actions" style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
        <button onClick={() => onSave(currentSectionIndex, draftText)} disabled={isLoading}>
          Save
        </button>
        <button
          onClick={() => onInsert(draftText)}
          disabled={!editorStatus.detected || isLoading}
        >
          Insert
        </button>
      </div>

      <div className="section-chat">
        {chats.map((msg, i) => (
          <div
            key={i}
            data-testid={`section-chat-message-${i}`}
            data-role={msg.role}
            className={`chat-bubble chat-bubble--${msg.role}`}
          >
            {msg.content}
          </div>
        ))}

        <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
          <input
            type="text"
            aria-label="Refine"
            value={refineInput}
            onChange={(e) => setRefineInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
            placeholder="Ask for changes…"
            style={{ flex: 1 }}
          />
          <button onClick={handleSend} disabled={isLoading} aria-label="Refine">
            Refine
          </button>
        </div>
      </div>
    </div>
  );
}
