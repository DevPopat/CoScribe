import React, { useState } from "react";
import type { Outline } from "../../types";
import type { RefinementMessage } from "../hooks/useSession";
import RefineChat from "./RefineChat";

interface OutlineViewProps {
  outline: Outline;
  currentSectionIndex: number;
  onSelectSection: (index: number) => void;
  refinementHistory: RefinementMessage[];
  isRefining: boolean;
  outlineChanged: boolean;
  onRefine: (message: string) => void;
  onOutlineTabClick: () => void;
}

export default function OutlineView({
  outline,
  currentSectionIndex,
  onSelectSection,
  refinementHistory,
  isRefining,
  outlineChanged,
  onRefine,
  onOutlineTabClick,
}: OutlineViewProps) {
  const [activeTab, setActiveTab] = useState<"outline" | "refine">("outline");

  const handleOutlineTab = () => {
    setActiveTab("outline");
    onOutlineTabClick();
  };

  return (
    <div className="outline-view">
      <div className="outline-tabs" data-testid="outline-tabs">
        <button
          onClick={handleOutlineTab}
          data-testid="tab-outline"
          style={{ fontWeight: activeTab === "outline" ? "bold" : "normal" }}
        >
          Outline{outlineChanged && activeTab !== "outline" ? " \u2022" : ""}
        </button>
        <button
          onClick={() => setActiveTab("refine")}
          data-testid="tab-refine"
          style={{ fontWeight: activeTab === "refine" ? "bold" : "normal" }}
        >
          Refine
        </button>
      </div>

      {activeTab === "outline" && (
        <div data-testid="outline-content">
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
      )}

      {activeTab === "refine" && (
        <RefineChat
          history={refinementHistory}
          isRefining={isRefining}
          onSend={onRefine}
        />
      )}
    </div>
  );
}
