import React from "react";
import useSession from "./hooks/useSession";
import useEditorStatus from "./hooks/useEditorStatus";
import TopicForm from "./components/TopicForm";
import OutlineView from "./components/OutlineView";
import SectionDraft from "./components/SectionDraft";
import EditorStatus from "./components/EditorStatus";

export default function App() {
  const {
    session,
    outline,
    currentSectionIndex,
    isLoading,
    error,
    startSession,
    draftSection,
    approveSection,
  } = useSession();

  const editorStatus = useEditorStatus();

  const handleInsert = (text: string) => {
    chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
      if (tab?.id) {
        chrome.tabs.sendMessage(tab.id, { type: "INSERT_TEXT", text });
      }
    });
  };

  // Before plan: show form
  if (!outline) {
    return (
      <div className="app">
        <h1>CoScribe</h1>
        {error && <p className="error">{error}</p>}
        <TopicForm onSubmit={startSession} isLoading={isLoading} />
        <EditorStatus status={editorStatus} />
      </div>
    );
  }

  const activeSection = outline.sections[currentSectionIndex];

  // After plan: show outline + section draft
  return (
    <div className="app">
      <h1>CoScribe</h1>
      {error && <p className="error">{error}</p>}
      {session?.status === "complete" && <p>All sections complete!</p>}

      <OutlineView
        outline={outline}
        currentSectionIndex={currentSectionIndex}
        onSelectSection={(i) => draftSection(i)}
      />

      {activeSection && (
        <SectionDraft
          section={activeSection}
          sectionIndex={currentSectionIndex}
          editorStatus={editorStatus}
          isLoading={isLoading}
          onDraft={draftSection}
          onApprove={approveSection}
          onInsert={handleInsert}
        />
      )}

      <EditorStatus status={editorStatus} />
    </div>
  );
}
