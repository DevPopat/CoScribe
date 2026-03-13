import React, { useState } from "react";
import type { RefinementMessage } from "../hooks/useSession";

interface RefineChatProps {
  history: RefinementMessage[];
  isRefining: boolean;
  onSend: (message: string) => void;
}

export default function RefineChat({ history, isRefining, onSend }: RefineChatProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setInput("");
  };

  return (
    <div className="refine-chat" data-testid="refine-chat">
      <div className="refine-history" data-testid="refine-history">
        {history.map((msg, i) => (
          <div key={i} data-testid={`refine-msg-${i}`} className={`refine-msg refine-msg-${msg.role}`}>
            <strong>{msg.role === "user" ? "You" : "CoScribe"}:</strong> {msg.content}
          </div>
        ))}
        {isRefining && <div data-testid="refine-loading">Thinking…</div>}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for changes to the outline…"
          disabled={isRefining}
          aria-label="Refinement message"
        />
        <button type="submit" disabled={isRefining || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
