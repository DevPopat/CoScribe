"""
Plan generation, refinement, and section drafting API endpoints.

Provides POST /sessions/{id}/plan to run the planning agents,
POST /sessions/{id}/plan/refine to iteratively edit the outline,
POST /sessions/{id}/sections/{n}/draft to draft a single section,
POST /sessions/{id}/sections/{n}/approve to approve (or edit) a draft, and
POST /sessions/{id}/sections/{n}/refine to refine a draft based on feedback.
"""

import asyncio
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents.drafter import draft_section
from app.agents.refine import refine_outline
from app.agents.section_refine import refine_section
from app.agents.research import research_topic
from app.agents.style_analyzer import analyze_style
from app.agents.synthesizer import synthesize_outline
from app.deps import get_store
from app.store.base import SessionStore

router = APIRouter(prefix="/sessions", tags=["drafts"])


@router.post("/{session_id}/plan")
async def generate_plan(
    session_id: str, store: SessionStore = Depends(get_store)
) -> dict:
    """
    Run the planning agents and store the resulting outline on the session.

    Phase 1 runs research (Anthropic) and style analysis (OpenAI) concurrently
    since they draw from separate rate-limit pools.  Phase 2 feeds their
    outputs into the synthesizer to produce a structured outline.

    :param session_id: The UUID of the session to plan.
    :param store: Injected session store.
    :returns: The generated outline as a dict.
    :raises HTTPException: 404 if the session does not exist.
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "planning"
    store.update(session)

    # Phase 1: research (Anthropic) and style analysis (OpenAI) run concurrently
    # since they draw from separate rate-limit pools.
    research_result, style_result = await asyncio.gather(
        asyncio.to_thread(research_topic, session.topic, session.audience, session.notes),
        asyncio.to_thread(analyze_style, session.writing_samples, session.reference_urls),
    )

    # Phase 2: synthesize outline from research + style
    outline = await asyncio.to_thread(
        synthesize_outline,
        session.topic,
        session.audience,
        research_result["summary"],
        style_result,
        research_urls=research_result["urls"],
    )

    session.outline = outline
    session.status = "outline_ready"
    store.update(session)

    return outline.model_dump()


class RefineRequest(BaseModel):
    """
    Request body for refining an existing outline.

    :param message: The user's refinement instruction.
    """

    message: str


@router.post("/{session_id}/plan/refine")
async def refine_plan(
    session_id: str,
    body: RefineRequest,
    store: SessionStore = Depends(get_store),
) -> dict:
    """
    Refine the session's outline based on user feedback.

    Appends the user message to refinement_history, calls the refine agent,
    updates the stored outline, and appends the assistant reply to history.
    Session status stays ``outline_ready`` throughout.

    :param session_id: The UUID of the session to refine.
    :param body: The user's refinement message.
    :param store: Injected session store.
    :returns: A dict with ``outline`` and ``reply`` keys.
    :raises HTTPException: 404 if the session does not exist, 400 if no
        outline has been generated yet.
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.outline is None:
        raise HTTPException(status_code=400, detail="No outline to refine — run /plan first")

    session.refinement_history.append({"role": "user", "content": body.message})

    updated_outline, reply = await asyncio.to_thread(
        refine_outline, session.outline, session.refinement_history, body.message
    )

    session.outline = updated_outline
    session.refinement_history.append({"role": "assistant", "content": reply})
    store.update(session)

    return {"outline": updated_outline.model_dump(), "reply": reply}


def _get_section(session, section_index: int):
    """
    Validate and return a section from the session's outline.

    :param session: The writing session.
    :param section_index: Zero-based section index.
    :returns: The section at the given index.
    :raises HTTPException: 400 if no outline exists, 404 if index is out of range.
    """
    if session.outline is None:
        raise HTTPException(status_code=400, detail="No outline — run /plan first")
    if section_index < 0 or section_index >= len(session.outline.sections):
        raise HTTPException(status_code=404, detail="Section index out of range")
    return session.outline.sections[section_index]


@router.post("/{session_id}/sections/{section_index}/draft")
async def draft_section_endpoint(
    session_id: str,
    section_index: int,
    store: SessionStore = Depends(get_store),
) -> dict:
    """
    Draft a single section of the article using Claude.

    Sets session status to ``drafting`` on the first draft request.

    :param session_id: The UUID of the session.
    :param section_index: Zero-based index of the section to draft.
    :param store: Injected session store.
    :returns: A dict with the ``draft`` text.
    :raises HTTPException: 404 if session or section not found, 400 if no outline.
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    section = _get_section(session, section_index)

    if session.status == "outline_ready":
        session.status = "drafting"

    draft = await asyncio.to_thread(
        draft_section,
        session.outline.title,
        session.outline.brief,
        session.outline.tone_guidance,
        section.title,
        section.key_points,
    )

    section.draft = draft
    store.update(session)

    return {"draft": draft}


class ApproveRequest(BaseModel):
    """
    Optional request body for approving a section draft.

    :param text: If provided, replaces the draft with user-edited text before approving.
    """

    text: Optional[str] = None


@router.post("/{session_id}/sections/{section_index}/approve")
def approve_section(
    session_id: str,
    section_index: int,
    body: ApproveRequest = ApproveRequest(),
    store: SessionStore = Depends(get_store),
) -> dict:
    """
    Mark a section as approved, optionally replacing the draft text.

    When all sections are approved the session status moves to ``complete``.

    :param session_id: The UUID of the session.
    :param section_index: Zero-based index of the section to approve.
    :param body: Optional edited text to replace the current draft.
    :param store: Injected session store.
    :returns: A dict with ``approved`` status and section index.
    :raises HTTPException: 404 if session or section not found, 400 if no
        outline or no draft to approve.
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    section = _get_section(session, section_index)

    if section.draft is None and body.text is None:
        raise HTTPException(status_code=400, detail="No draft to approve — run /draft first")

    if body.text is not None:
        section.draft = body.text
    section.approved = True

    if all(s.approved for s in session.outline.sections):
        session.status = "complete"

    store.update(session)

    return {"approved": True, "section_index": section_index}


class SectionRefineRequest(BaseModel):
    """
    Request body for refining a section draft.

    :param message: The user's feedback or refinement instruction.
    :param current_draft: The current draft text to refine.
    """

    message: str
    current_draft: str


@router.post("/{session_id}/sections/{section_index}/refine")
async def refine_section_endpoint(
    session_id: str,
    section_index: int,
    body: SectionRefineRequest,
    store: SessionStore = Depends(get_store),
) -> dict:
    """
    Refine a section draft based on user feedback.

    Calls the section_refine agent with the current draft and user message,
    stores the updated draft on the section, and optionally updates the
    section's key_points and sources if the agent returns changes.

    :param session_id: The UUID of the session.
    :param section_index: Zero-based index of the section to refine.
    :param body: The user's feedback message and current draft text.
    :param store: Injected session store.
    :returns: A dict with ``draft``, ``key_points``, ``sources``, and ``reply`` keys.
    :raises HTTPException: 404 if session or section not found, 400 if no outline.
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    section = _get_section(session, section_index)

    updated_draft, updated_key_points, updated_sources, reply = await asyncio.to_thread(
        refine_section,
        session.outline.title,
        session.outline.brief,
        session.outline.tone_guidance,
        section.title,
        section.key_points,
        section.sources,
        body.current_draft,
        body.message,
    )

    section.draft = updated_draft
    if updated_key_points is not None:
        section.key_points = updated_key_points
    if updated_sources is not None:
        section.sources = updated_sources
    store.update(session)

    return {
        "draft": updated_draft,
        "key_points": updated_key_points,
        "sources": updated_sources,
        "reply": reply,
    }
