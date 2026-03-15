# CoScribe Chat UI Redesign

## Overview

Replace the current multi-panel extension UI (TopicForm, OutlineView, SectionDraft) with a unified chat-first interface. Users describe their writing project conversationally, CoScribe asks clarifying questions, generates a structured outline, and supports iterative drafting — all within a single chat flow.

## Goals

- Eliminate separate input forms and disconnected views
- Provide a natural, conversational experience similar to ChatGPT Deep Research
- Keep the outline toggle-between-sections feature users like
- Support iterative refinement at both outline and section draft level
- Persist session state across panel close/reopen

## Architecture Approach

**Hybrid (Approach 3):** One new backend endpoint (`/sessions/chat`) handles conversational intake. All existing endpoints (`/plan`, `/draft`, `/refine`, `/approve`) remain unchanged. A second new endpoint (`/sections/{n}/refine`) handles per-section draft refinement. The frontend is restructured but the backend changes are minimal.

## UI Structure

### Two Views

The UI has two views controlled by a `current_view` state variable:

1. **ChatView** (default) — the main chat interface handling intake, outline display, and outline-level refinement
2. **DraftView** — section editing with key points, sources, textarea editor, and per-section chat

### Header

Both views share a top header bar with:
- "CoScribe" branding on the left
- "+ New Session" button on the right (clears local storage, resets to ChatView with welcome message, prompts confirmation if any section is in `drafted` state — i.e., has unsaved edits)

## Phase 1: Conversational Intake

The chat opens with a centered welcome message: "Tell me about your writing project."

The user describes their project naturally in one message (topic, audience, samples, notes — whatever they want to include). CoScribe extracts structured fields from the message and only asks follow-up questions for genuinely missing information. This is handled by the new `/sessions/chat` endpoint.

When the AI determines it has enough info, it signals `ready: true` with extracted fields. The frontend then calls `POST /sessions` and `POST /sessions/{id}/plan` to create the session and generate the outline.

### Loading States

While agents are working, an animated loading bubble cycles through fun, personality-filled messages every 3 seconds:

- **During planning:** "Pondering...", "Researching...", "Snooping around the web...", "Concocting an outline...", "Brewing ideas..."
- **During drafting:** "Scribbling away...", "Wordsmithing...", "Crafting prose...", "Shimmying words into place..."
- **During refinement:** "Rethinking...", "Tinkering...", "Massaging the draft...", "Cooking up changes..."

## Phase 2: Outline Review & Refinement

The generated outline appears as an **inline card** in the chat stream (an `OutlineCard` component). The card contains:

- **Title** and **brief** summary
- **Expandable/collapsible sections** — each section shows:
  - Expand/collapse arrow
  - Section title
  - "Draft →" button
  - When expanded: bulleted key points
  - When expanded: collapsible "Sources (N)" accordion showing URLs the research agent fetched (collapsed by default)

The user can refine the outline by chatting below the card ("add a section about async communication"). Refinement messages go through the existing `POST /sessions/{id}/plan/refine` endpoint. When the outline updates, the inline card updates in place.

## Phase 3: Section Drafting & Editing

Clicking "Draft →" on any section transitions to **DraftView**. This view contains:

### Section Navigation

- **Back button** (← arrow) returns to ChatView, scrolled to the outline card
- **Section title** displayed next to back button
- **Pill-style horizontal nav bar** below the header for switching between sections without returning to the outline. Pills show:
  - Empty circle — no draft yet
  - Filled circle — drafted/in-progress
  - Checkmark — saved

### Section Content

- **Key Points panel** — the section's outline points, displayed in a compact panel
- **Sources accordion** — same per-section sources from the outline card, collapsible, sits between key points and editor
- **Plain textarea editor** — the generated draft appears here. User can directly edit the text. No rich text formatting.
- **Action buttons:**
  - **Save** — locks/saves the draft text
  - **Insert** — pushes the text to the detected page editor via content script. Shows editor detection status (green dot + adapter name when detected, disabled when no editor found)

### Per-Section Chat

Below the editor, a "Section Chat" area provides a dedicated chat thread for refining this specific section. Examples: "add a statistic about productivity", "make the intro punchier", "add a joke here".

Messages go through the new `POST /sessions/{id}/sections/{n}/refine` endpoint. When the AI responds, the draft in the textarea updates with the changes, and key points/sources may also update if the changes warrant it.

Each section maintains its own independent chat history, persisted to local storage.

## Components

### New Components (replacing current ones)

| Component | Purpose |
|-----------|---------|
| **App** | Root component. Manages which view is shown (chat vs draft), holds session state via `useSession` hook |
| **ChatView** | Main chat interface. Renders message history with different bubble types: user (right-aligned), assistant (left-aligned), outline card (full-width), loading bubble |
| **OutlineCard** | Inline chat component. Expandable sections with key points, sources accordion, "Draft →" buttons. Updates in place when outline is refined |
| **DraftView** | Section editing view. Composes SectionNav, key points panel, sources accordion, textarea editor, action buttons, and per-section chat |
| **SectionNav** | Pill-style horizontal nav bar for switching sections. Shows draft status indicators |
| **LoadingBubble** | Animated assistant bubble that cycles through fun status messages |
| **EditorStatus** | Kept from current codebase. Shown near the Insert button in DraftView |

### Components Removed

- **TopicForm** — replaced by conversational intake in ChatView
- **OutlineView** — replaced by OutlineCard inline in chat
- **SectionDraft** — replaced by DraftView
- **RefineChat** — replaced by the chat interface itself (both main chat and per-section chat)

## Hooks

| Hook | Changes |
|------|---------|
| **useSession** | Refactored to manage: main chat history, per-section chat histories, current view state, current section index. New methods: `sendChatMessage(message: string) => Promise<void>` (sends to `/sessions/chat`, handles `ready` flag by creating session + generating plan), `refineSectionDraft(sectionIndex: number, message: string) => Promise<void>` (sends to `/sections/{n}/refine` with current draft text, updates draft/key_points/sources in state, appends to per-section chat history). Existing methods kept: `draftSection()`, `approveSection()`, `refineOutline()` |
| **useAPI** | Extended with new endpoints: `POST /sessions/chat`, `POST /sessions/{id}/sections/{n}/refine` |
| **useEditorStatus** | Unchanged |
| **useLocalStorage** | New hook for persisting session state. Uses `chrome.storage.local` when running as an extension (checks for `chrome.storage` availability), falls back to `localStorage` for dev/testing |

## API Changes

### New: `POST /sessions/chat` (in `api/chat.py`, new router)

Handles conversational intake. The backend AI analyzes the message, determines if it has enough info to create a session, and either asks a follow-up or signals readiness. Uses a new `intake` agent (`agents/intake.py`) with a system prompt instructing it to extract topic, audience, notes, writing_samples, and reference_urls from natural language and return a structured JSON response.

```
Request: {
  messages: [{ role: "user" | "assistant", content: string }]
}

Response: {
  reply: string,
  ready: boolean,
  extracted?: {
    topic: string,
    audience: string,
    notes?: string,
    writing_samples?: string[],
    reference_urls?: string[]
  }
}
```

### New: `POST /sessions/{id}/sections/{n}/refine`

Handles per-section draft refinement. Receives the user's feedback and current draft, returns updated draft and optionally updated key points/sources.

```
Request: {
  message: string,
  current_draft: string
}

Response: {
  draft: string,
  key_points?: string[],
  sources?: string[],
  reply: string
}
```

### Modified: Data Models

**Section model** gains a `sources` field:

```python
class Section(BaseModel):
    title: str
    key_points: list[str]
    sources: list[str] = []   # NEW — URLs from research agent
    draft: str | None = None
    approved: bool = False
```

**Research agent** changes:
- `research_topic()` return type changes from `str` to a structured dict: `{ "summary": str, "urls": list[str] }`. The agent's system prompt is updated to instruct it to include fetched URLs in its output. `run_agent_loop()` is unchanged — the research agent's prompt asks it to format its final response as JSON with `summary` and `urls` fields.
- `drafts.py` (`generate_plan`) parses the structured return and passes both summary and URLs to the synthesizer.

**Synthesizer agent** changes:
- `synthesize_outline()` receives a `research_urls: list[str]` parameter alongside the existing `research` text.
- `_OUTLINE_SCHEMA` is updated to include `"sources": ["string"]` in each section object.
- The synthesizer prompt instructs the model to distribute relevant source URLs across sections.

**Refine agent** changes:
- `_OUTLINE_SCHEMA` in `refine.py` is updated to include `"sources": ["string"]` per section, matching the synthesizer schema.

### TypeScript Type Updates

The following types in `extension/src/types.ts` must be updated:

```typescript
// Updated
interface Section {
  title: string;
  key_points: string[];
  sources: string[];        // NEW
  draft: string | null;
  approved: boolean;
}

// New types
interface ChatRequest {
  messages: { role: "user" | "assistant"; content: string }[];
}

interface ChatResponse {
  reply: string;
  ready: boolean;
  extracted?: {
    topic: string;
    audience: string;
    notes?: string;
    writing_samples?: string[];
    reference_urls?: string[];
  };
}

interface SectionRefineRequest {
  message: string;
  current_draft: string;
}

interface SectionRefineResponse {
  draft: string;
  key_points?: string[];
  sources?: string[];
  reply: string;
}
```

### Unchanged Endpoints

- `POST /sessions` — creates session with extracted fields
- `GET /sessions/{id}` — retrieves session
- `POST /sessions/{id}/plan` — generates outline (now includes sources per section)
- `POST /sessions/{id}/plan/refine` — outline-level refinement
- `POST /sessions/{id}/sections/{n}/draft` — generates section draft
- `POST /sessions/{id}/sections/{n}/approve` — approves section

## Local Storage Schema

```typescript
interface PersistedState {
  session_id: string | null;
  chat_history: Message[];
  outline: Outline | null;
  section_chats: { [sectionIndex: number]: Message[] };
  section_drafts: { [sectionIndex: number]: string };
  current_view: "chat" | "draft";
  current_section: number;
}
```

Stored under key `coscribe_session`. Loaded on panel open, saved on every state change. "New Session" button clears this and resets all state.

## State Machine

### Section Draft States

```
empty → generating → drafted → saved
  ↑          ↑          |         |
  |          └──────────┘         |
  |    (chat refinement from      |
  |     drafted shows loading     |
  |     then returns to drafted)  |
  |                               |
  |          ↑────────────────────┘
  |    (chat refinement from saved
  |     shows loading, unlocks,
  |     returns to drafted)
  └── (no transitions back to empty)
```

- **empty** — no draft, "Draft" button shown in outline card
- **generating** — loading bubble with fun messages (cycles every 3 seconds)
- **drafted** — text in editor, user can edit, Save and Insert available
- **saved** — text locked (visually indicated), Insert available, "Edit" button to unlock
- Chat refinement from **drafted** → shows generating state → returns to **drafted** with updated text
- Chat refinement from **saved** → shows generating state → unlocks and returns to **drafted** with updated text

### Section Nav Indicators

- Empty circle (○) — no draft
- Filled circle (●) — drafted/in-progress
- Checkmark (✓) — saved

## Error Handling

Errors are shown as assistant-style chat bubbles with a red accent and a "Retry" button.

- **During intake (`/sessions/chat` failure):** Error bubble appears in the main chat. User can retry their last message or type a new one.
- **During plan generation (`/sessions` or `/plan` failure after `ready: true`):** Error bubble in main chat with "Retry" button that re-triggers session creation and plan generation with the same extracted fields.
- **During drafting (`/sections/{n}/draft` failure):** Error bubble in the per-section chat. "Retry" button re-triggers draft generation.
- **During section refinement (`/sections/{n}/refine` failure):** Error bubble in the per-section chat. "Retry" button re-sends the last refinement message.
- **During outline refinement (`/plan/refine` failure):** Error bubble in the main chat. "Retry" button re-sends the last refinement message.

All retry buttons re-send the exact same request. The user can also just type a new message to continue the conversation, which implicitly abandons the failed request.

## Content Script & Editor Adapters

No changes to the content script, editor adapter interface, or adapter registry. The existing tier-based system (Tier 1: rich API, Tier 2: clipboard simulation, Tier 3: DOM fallback) continues to work as-is. The Insert button in DraftView sends the same `INSERT_TEXT` message as the current implementation.

## What This Design Does NOT Include

- Rich text editor (plain textarea only — can upgrade later)
- Completion ceremony when all sections are done
- Multiple session management (one session at a time, "New Session" clears current)
- Markdown rendering or conversion
- Backend persistence (local storage only for chat/draft state; backend remains in-memory)
