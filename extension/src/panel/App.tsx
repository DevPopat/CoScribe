// Root panel component. Routes between ChatView (intake) and DraftView
// (section editing) based on currentView from useSession.

import React, { useState } from "react";
import useSession from "./hooks/useSession";
import useEditorStatus from "./hooks/useEditorStatus";
import ChatView from "./components/ChatView";
import DraftView from "./components/DraftView";

export default function App() {
  const [darkMode, setDarkMode] = useState(false);

  const {
    outline,
    currentSectionIndex,
    currentView,
    isLoading,
    error,
    chatHistory,
    sectionChats,
    sendChatMessage,
    draftSection,
    approveSection,
    refineSectionDraft,
    clearSession,
  } = useSession();

  const editorStatus = useEditorStatus();

  const handleInsert = (text: string) => {
    chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, { type: "INSERT_TEXT", text });
      }
    });
  };

  const handleNewSession = () => {
    const hasDraft = outline?.sections.some((s) => s.draft !== null);
    if (hasDraft) {
      const ok = window.confirm("You have unsaved drafts. Start a new session anyway?");
      if (!ok) return;
    }
    clearSession();
    window.location.reload();
  };

  return (
    <div className="app" style={{ display: "flex", flexDirection: "column", height: "100vh", background: darkMode ? "#1c1c1e" : "#fff", color: darkMode ? "#fff" : "#1c1c1e" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", borderBottom: `1px solid ${darkMode ? "#444" : "#ddd"}` }}>
        <h1 style={{ margin: 0, fontSize: "1rem" }}>CoScribe</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.75rem" }} title={editorStatus.detected ? `Editor detected: ${editorStatus.tier}` : "No editor detected"}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: editorStatus.detected ? "#27AE60" : "#999", display: "inline-block" }} />
            {editorStatus.detected ? "Editor" : "No editor"}
          </span>
          <label style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.8rem", cursor: "pointer" }}>
            <input type="checkbox" checked={darkMode} onChange={(e) => setDarkMode(e.target.checked)} />
            Dark
          </label>
          <button onClick={handleNewSession}>+ New Session</button>
        </div>
      </header>

      <div style={{ flex: 1, overflow: "hidden" }}>
        {currentView === "chat" && (
          <ChatView
            chatHistory={chatHistory}
            outline={outline}
            isLoading={isLoading}
            darkMode={darkMode}
            onSend={sendChatMessage}
            onDraft={draftSection}
          />
        )}

        {currentView === "draft" && outline && (
          <DraftView
            outline={outline}
            currentSectionIndex={currentSectionIndex}
            sectionChats={sectionChats}
            editorStatus={editorStatus}
            isLoading={isLoading}
            error={error}
            onBack={() => window.location.reload()}
            onSelectSection={(i) => draftSection(i)}
            onSave={(i, text) => approveSection(i, text)}
            onInsert={handleInsert}
            onRefineDraft={refineSectionDraft}
          />
        )}
      </div>
    </div>
  );
}
