// Pill-style horizontal nav bar for switching between outline sections.
// Each pill shows the section title and a status indicator:
//   empty    — no draft yet
//   drafted  — draft exists but not approved
//   approved — section approved

import React from "react";
import type { Section } from "../../types";

interface SectionNavProps {
  sections: Section[];
  currentIndex: number;
  onSelect: (index: number) => void;
}

function statusOf(section: Section): "empty" | "drafted" | "approved" {
  if (section.approved) return "approved";
  if (section.draft !== null) return "drafted";
  return "empty";
}

const STATUS_ICON: Record<"empty" | "drafted" | "approved", string> = {
  empty: "○",
  drafted: "●",
  approved: "✓",
};

export default function SectionNav({ sections, currentIndex, onSelect }: SectionNavProps) {
  return (
    <nav
      className="section-nav"
      style={{ display: "flex", overflowX: "auto", gap: "6px", padding: "6px 0" }}
    >
      {sections.map((section, i) => {
        const status = statusOf(section);
        const isActive = i === currentIndex;
        return (
          <button
            key={i}
            aria-current={isActive ? "true" : undefined}
            className={`section-pill${isActive ? " section-pill--active" : ""}`}
            onClick={() => onSelect(i)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px 10px",
              borderRadius: "999px",
              border: "1px solid",
              cursor: "pointer",
              whiteSpace: "nowrap",
              fontWeight: isActive ? 600 : 400,
            }}
          >
            <span
              data-testid={`section-status-${i}`}
              data-status={status}
              aria-hidden="true"
            >
              {STATUS_ICON[status]}
            </span>
            {section.title}
          </button>
        );
      })}
    </nav>
  );
}
