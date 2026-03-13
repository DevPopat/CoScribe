import React from "react";
import type { Outline } from "../../types";

interface OutlineViewProps {
  outline: Outline;
  currentSectionIndex: number;
  onSelectSection: (index: number) => void;
}

export default function OutlineView({
  outline,
  currentSectionIndex,
  onSelectSection,
}: OutlineViewProps) {
  return (
    <div className="outline-view">
      <h2>{outline.title}</h2>
      <p>{outline.brief}</p>
      <ul>
        {outline.sections.map((section, i) => (
          <li
            key={i}
            data-testid={`section-item-${i}`}
            style={{ fontWeight: i === currentSectionIndex ? "bold" : "normal" }}
          >
            <button
              onClick={() => onSelectSection(i)}
              style={{ all: "unset", cursor: "pointer" }}
            >
              {section.approved ? "\u2713 " : "\u25CB "}
              {section.title}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
