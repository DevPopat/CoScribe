// Assistant-style chat bubble that cycles through contextual status messages
// every 3 seconds based on the current phase. Text color shifts randomly on
// each message change for a lively feel.

import React, { useEffect, useState } from "react";

type Phase = "planning" | "drafting" | "refining";

const MESSAGES: Record<Phase, string[]> = {
  planning: [
    "Pondering",
    "Researching",
    "Snooping around the web",
    "Concocting an outline",
    "Brewing ideas",
  ],
  drafting: [
    "Scribbling away",
    "Wordsmithing",
    "Crafting prose",
    "Shimmying words into place",
  ],
  refining: [
    "Rethinking",
    "Tinkering",
    "Massaging the draft",
    "Cooking up changes",
  ],
};

const COLORS = [
  "#9B59B6", // purple
  "#3498DB", // blue
  "#27AE60", // green
  "#E67E22", // orange
  "#E91E8C", // pink
  "#1ABC9C", // teal
  "#E74C3C", // red
  "#F39C12", // amber
];

function randomColor(exclude?: string): string {
  const candidates = COLORS.filter((c) => c !== exclude);
  return candidates[Math.floor(Math.random() * candidates.length)];
}

interface LoadingBubbleProps {
  phase: Phase;
}

export default function LoadingBubble({ phase }: LoadingBubbleProps) {
  const messages = MESSAGES[phase];
  const [index, setIndex] = useState(0);
  const [color, setColor] = useState(() => randomColor());

  useEffect(() => {
    setIndex(0);
    setColor(randomColor());
    const id = setInterval(() => {
      setIndex((prev) => (prev + 1) % messages.length);
      setColor((prev) => randomColor(prev));
    }, 3000);
    return () => clearInterval(id);
  }, [phase, messages.length]);

  return (
    <div
      className="loading-bubble"
      data-testid="loading-bubble"
      role="status"
      aria-live="polite"
      style={{
        display: "inline-block",
        maxWidth: "75%",
        padding: "8px 12px",
        borderRadius: "16px 16px 16px 4px",
        background: "#E9E9EB",
        fontSize: "0.875rem",
        lineHeight: "1.4",
      }}
    >
      <span style={{ color, fontStyle: "italic", transition: "color 0.4s ease" }}>
        {messages[index]} …
      </span>
    </div>
  );
}
