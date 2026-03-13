"""
Plan generation and section drafting API endpoints.

Provides POST /sessions/{id}/plan which runs the planning agents and
stores the resulting outline on the session.
"""

import asyncio
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

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
