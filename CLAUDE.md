# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CoScribe is a writer's copilot browser extension + backend API. Users enter a topic and writing samples, AI planning agents generate a structured outline, and the extension drafts one section at a time — inserting approved content directly into any supported web editor.

## Development Commands

### Backend (Python + FastAPI)

```bash
# Start the backend
docker compose up backend

# Run all tests
docker compose run --rm backend pytest tests/ -v

# Run a single test file
docker compose run --rm backend pytest tests/test_sessions.py -v

# Run a single test
docker compose run --rm backend pytest tests/test_sessions.py::test_create_session -v
```

Copy `backend/.env.example` to `backend/.env` and set `ANTHROPIC_API_KEY` before starting.

### Extension (React + TypeScript + Vite)

```bash
cd extension
npm install

# Dev build with watch
npm run dev

# Production build
npm run build

# Run tests
npm test

# Run a single test file
npx vitest run src/panel/hooks/useSession.test.ts
```

### Loading the Extension in Chrome

1. Run `npm run build` in `extension/`
2. Open `chrome://extensions/`
3. Enable Developer mode → Load unpacked → select `extension/dist/`

## Architecture

### Data Flow

```
User (Topic + Samples)
  → TopicForm (extension panel)
  → POST /sessions + POST /sessions/{id}/plan (backend)
  → 4 Planning Agents (sequential): Research → Style Analyzer → Coverage Gap → Synthesizer
  → Outline returned to OutlineView
  → User edits/approves outline
  → POST /sessions/{id}/sections/{n}/draft (backend)
  → SectionDraft component shows draft
  → User approves → content script injects text into page editor
```

### Backend (`backend/app/`)

- `main.py` — FastAPI app, CORS, router registration
- `api/sessions.py` — Session CRUD endpoints
- `api/drafts.py` — Plan generation (`POST /plan`) and section drafting endpoints
- `agents/` — Four planning agents called sequentially: `research.py`, `style_analyzer.py`, `coverage_gap.py`, `synthesizer.py`
- `models/session.py` — `WritingSession` dataclass; `models/outline.py` — Pydantic `Outline` + `Section`
- `store/base.py` — Abstract `SessionStore` interface; `store/memory.py` — in-memory dict implementation
- `deps.py` — Dependency injection: provides store instance to all routes

The repository pattern in `store/` lets the in-memory MVP store be swapped for SQLite/Postgres without touching API code.

### Extension (`extension/src/`)

- `panel/` — Side panel React app (`TopicForm` → `OutlineView` → `SectionDraft`)
- `panel/hooks/useSession.ts` — All session state and API calls; `useAPI.ts` — typed HTTP client
- `content/` — Content script injected into web pages; detects editable targets and inserts approved sections
- `content/editors/` — Pluggable editor adapters (`contenteditable.ts`, `textarea.ts`); register new adapters here to support additional editors
- `background/` — Service worker; relays messages between panel and content script

The extension uses Chrome Manifest V3. Edge is supported for free; Firefox is a follow-up task (separate manifest).

## Key Patterns

- **Agent model**: `claude-sonnet-4-6` via Anthropic SDK. Each agent receives the previous agent's output as additional context.
- **Session state machine**: sessions move through `pending → planning → outline_ready → drafting → complete`.
- **Editor adapters**: `content/editors/base.ts` defines the abstract interface. The content script uses a registry to pick the right adapter at runtime.
- **In-memory store**: MVP only — all session data is lost on server restart. Store is abstracted for future persistence.

## Issue Tracking

This project uses **Beads** (`bd`) for issue tracking — a Git-native, Dolt-backed system.

```bash
bd ready                  # find work with no blockers
bd show <id>              # view issue detail
bd update <id> --status=in_progress
bd close <id>
```

See `AGENTS.md` for full workflow.

**Standalone tickets**: Any ticket that has no natural place in the dependency tree must be linked as a dependency of `CoScribe-tc7` so it appears in the graph:

```bash
bd dep add CoScribe-tc7 <new-ticket-id>
```

## Git Workflow

After completing any task, always run this sequence:

1. Commit and push code changes
2. Close the beads ticket (`bd close <id>`)
3. Run `bd ready` to show the next available tasks

```bash
git add <files>
git commit -m "type(scope): description"
git push
```

## Code Documentation Standards

**Python files:**
- Module-level docstring at the top of every file explaining what it does.
- Sphinx-format docstrings on all functions, methods, and classes using `:param name:` and `:returns:`. Do **not** include `:type:` or `:rtype:` — type annotations on the signature are sufficient.

```python
def get(self, session_id: str) -> Optional[WritingSession]:
    """
    Retrieve a session by its ID.

    :param session_id: The UUID of the session to look up.
    :returns: The matching session, or ``None`` if not found.
    """
```

**Non-Python files** (Dockerfile, docker-compose.yml, shell scripts, etc.):
- Add brief inline comments through the script where the intent isn't obvious. No header block needed.

## Commit Message Style

Format: `type(scope): description`

| Type     | Meaning                 |
| -------- | ----------------------- |
| feat     | new feature             |
| fix      | bug fix                 |
| docs     | documentation           |
| refactor | code restructure        |
| test     | tests                   |
| chore    | maintenance             |
| perf     | performance improvement |

