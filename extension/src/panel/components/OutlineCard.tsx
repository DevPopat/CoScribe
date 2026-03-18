// Expandable outline card showing title, brief, and per-section
// key points + sources accordions with a Draft button per section.

import React, { useState } from "react";
import type { Outline } from "../../types";

interface OutlineCardProps {
  outline: Outline;
  onDraft: (sectionIndex: number) => void;
}

export default function OutlineCard({ outline, onDraft }: OutlineCardProps) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [sourcesOpen, setSourcesOpen] = useState<Record<number, boolean>>({});

  const toggleSection = (i: number) =>
    setExpanded((prev) => ({ ...prev, [i]: !prev[i] }));

  const toggleSources = (i: number) =>
    setSourcesOpen((prev) => ({ ...prev, [i]: !prev[i] }));

  return (
    <div className="outline-card" data-testid="outline-card">
      <h2>{outline.title}</h2>
      <p>{outline.brief}</p>

      {outline.sections.map((section, i) => (
        <div key={i} className="outline-section">
          <div className="outline-section-header" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              data-testid={`toggle-section-${i}`}
              aria-expanded={!!expanded[i]}
              onClick={() => toggleSection(i)}
              style={{ all: "unset", cursor: "pointer" }}
            >
              {expanded[i] ? "▾" : "▸"} <span>{section.title}</span>
            </button>
            <button onClick={() => onDraft(i)}>Draft</button>
          </div>

          {expanded[i] && (
            <div className="outline-section-body" style={{ paddingLeft: "16px" }}>
              <ul>
                {section.key_points.map((kp, j) => (
                  <li key={j}>{kp}</li>
                ))}
              </ul>

              {section.sources.length > 0 && (
                <div className="sources-accordion">
                  <button onClick={() => toggleSources(i)}>
                    Sources ({section.sources.length})
                  </button>
                  {sourcesOpen[i] && (
                    <ul>
                      {section.sources.map((url, k) => (
                        <li key={k}>{url}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
