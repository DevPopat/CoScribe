// Main intake chat interface. Renders message history with user/assistant
// bubbles, inline OutlineCard when the plan is ready, and a LoadingBubble
// during API calls. Chat input is pinned at the bottom.

import React, { useState } from "react";
import type { Outline } from "../../types";
import OutlineCard from "./OutlineCard";
import LoadingBubble from "./LoadingBubble";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatViewProps {
  chatHistory: Message[];
  outline: Outline | null;
  isLoading: boolean;
  onSend: (message: string) => void;
  onDraft?: (sectionIndex: number) => void;
}

export default function ChatView({
  chatHistory,
  outline,
  isLoading,
  onSend,
  onDraft,
}: ChatViewProps) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    onSend(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-view" data-testid="chat-view" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div className="chat-messages" style={{ flex: 1, overflowY: "auto", padding: "12px" }}>
        {chatHistory.length === 0 && !isLoading && (
          <div
            data-testid="welcome-message"
            className="welcome-message"
            style={{ textAlign: "center", opacity: 0.6, marginTop: "40px" }}
          >
            What would you like to write about?
          </div>
        )}

        {chatHistory.map((msg, i) => (
          <div
            key={i}
            data-testid={`message-${i}`}
            data-role={msg.role}
            className={`chat-bubble chat-bubble--${msg.role}`}
            style={{
              textAlign: msg.role === "user" ? "right" : "left",
              marginBottom: "8px",
            }}
          >
            {msg.content}
          </div>
        ))}

        {outline && (
          <div className="outline-inline" style={{ marginTop: "12px" }}>
            <OutlineCard outline={outline} onDraft={onDraft ?? (() => {})} />
          </div>
        )}

        {isLoading && <LoadingBubble phase="planning" />}
      </div>

      <div className="chat-input-row" style={{ display: "flex", gap: "8px", padding: "8px" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message…"
          style={{ flex: 1 }}
        />
        <button onClick={handleSend} disabled={!input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
