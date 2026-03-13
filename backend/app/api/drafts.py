"""
Plan generation, refinement, and section drafting API endpoints.

Provides POST /sessions/{id}/plan to run the planning agents and
POST /sessions/{id}/plan/refine to iteratively edit the outline.
"""

import asyncio
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents.refine import refine_outline
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

    Phase 1 runs research and style analysis concurrently.  Phase 2 feeds
    their outputs into the synthesizer to produce a structured outline.

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

    # Phase 1: research + style analysis in parallel
    research_result, style_result = await asyncio.gather(
        asyncio.to_thread(research_topic, session.topic, session.audience, session.notes),
        asyncio.to_thread(analyze_style, session.writing_samples, session.reference_urls),
    )

    # Phase 2: synthesize outline from research + style
    outline = await asyncio.to_thread(
        synthesize_outline, session.topic, session.audience, research_result, style_result
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
