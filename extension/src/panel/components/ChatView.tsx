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
  darkMode?: boolean;
  onSend: (message: string) => void;
  onDraft?: (sectionIndex: number) => void;
}

export default function ChatView({
  chatHistory,
  outline,
  isLoading,
  darkMode = false,
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
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
            style={{ textAlign: "center", opacity: 0.6, marginTop: "40px", color: darkMode ? "#fff" : "#1c1c1e" }}
          >
            What would you like to write about?
          </div>
        )}

        {chatHistory.map((msg, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              marginBottom: "8px",
            }}
          >
            <div
              data-testid={`message-${i}`}
              data-role={msg.role}
              className={`chat-bubble chat-bubble--${msg.role}`}
              style={{
                maxWidth: "75%",
                padding: "8px 12px",
                borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                background: msg.role === "user" ? "#007AFF" : darkMode ? "#3a3a3c" : "#E9E9EB",
                color: msg.role === "user" ? "#fff" : darkMode ? "#fff" : "#1c1c1e",
                fontSize: "0.875rem",
                lineHeight: "1.4",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {outline && (
          <div className="outline-inline" style={{ marginTop: "12px" }}>
            <OutlineCard outline={outline} onDraft={onDraft ?? (() => {})} />
          </div>
        )}

        {isLoading && <LoadingBubble phase="planning" />}
      </div>

      <div className="chat-input-row" style={{ display: "flex", gap: "8px", padding: "8px", alignItems: "flex-end" }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
          rows={3}
          style={{
            flex: 1,
            resize: "none",
            borderRadius: "8px",
            padding: "8px",
            fontSize: "0.875rem",
            background: darkMode ? "#2c2c2e" : "#fff",
            color: darkMode ? "#fff" : "#1c1c1e",
            border: `1px solid ${darkMode ? "#555" : "#ccc"}`,
          }}
        />
        <button onClick={handleSend} disabled={!input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
