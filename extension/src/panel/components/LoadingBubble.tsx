// Assistant-style chat bubble that cycles through contextual status messages
// every 3 seconds based on the current phase.

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

interface LoadingBubbleProps {
  phase: Phase;
}

export default function LoadingBubble({ phase }: LoadingBubbleProps) {
  const messages = MESSAGES[phase];
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
    const id = setInterval(() => {
      setIndex((prev) => (prev + 1) % messages.length);
    }, 3000);
    return () => clearInterval(id);
  }, [phase, messages.length]);

  return (
    <div
      className="loading-bubble"
      data-testid="loading-bubble"
      role="status"
      aria-live="polite"
    >
      {messages[index]} …
    </div>
  );
}
