import React from "react";
import type { Section, EditorStatus } from "../../types";

interface SectionDraftProps {
  section: Section;
  sectionIndex: number;
  editorStatus: EditorStatus;
  isLoading: boolean;
  onDraft: (index: number) => void;
  onApprove: (index: number) => void;
  onInsert: (text: string) => void;
}

export default function SectionDraft({
  section,
  sectionIndex,
  editorStatus,
  isLoading,
  onDraft,
  onApprove,
  onInsert,
}: SectionDraftProps) {
  const canInsert = editorStatus.detected && section.draft !== null;

  return (
    <div className="section-draft" data-testid="section-draft">
      <h3>{section.title}</h3>
      <ul>
        {section.key_points.map((kp, i) => (
          <li key={i}>{kp}</li>
        ))}
      </ul>

      {section.draft && (
        <div data-testid="draft-text" className="draft-text">
          {section.draft}
        </div>
      )}

      <div className="section-actions">
        <button
          onClick={() => onDraft(sectionIndex)}
          disabled={isLoading}
        >
          {section.draft ? "Regenerate" : "Draft"}
        </button>

        {section.draft && !section.approved && (
          <button
            onClick={() => onApprove(sectionIndex)}
            disabled={isLoading}
          >
            Approve
          </button>
        )}

        <button
          onClick={() => section.draft && onInsert(section.draft)}
          disabled={!canInsert || isLoading}
          title={
            !editorStatus.detected
              ? "No editor detected — copy the text manually"
              : undefined
          }
        >
          Insert
        </button>
      </div>
    </div>
  );
}
