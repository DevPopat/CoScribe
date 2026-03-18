// Root panel component. Routes between ChatView (intake) and DraftView
// (section editing) based on currentView from useSession.

import React from "react";
import useSession from "./hooks/useSession";
import useEditorStatus from "./hooks/useEditorStatus";
import ChatView from "./components/ChatView";
import DraftView from "./components/DraftView";

export default function App() {
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
    window.location.reload();
  };

  return (
    <div className="app" style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", borderBottom: "1px solid #ddd" }}>
        <h1 style={{ margin: 0, fontSize: "1rem" }}>CoScribe</h1>
        <button onClick={handleNewSession}>+ New Session</button>
      </header>

      <div style={{ flex: 1, overflow: "hidden" }}>
        {currentView === "chat" && (
          <ChatView
            chatHistory={chatHistory}
            outline={outline}
            isLoading={isLoading}
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
