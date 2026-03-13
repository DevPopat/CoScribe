"""
Session CRUD API endpoints.

Provides POST /sessions to create a new writing session and
GET /sessions/{id} to retrieve an existing one.
"""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.deps import get_store
from app.models.session import WritingSession
from app.store.base import SessionStore

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    """
    Request body for creating a new writing session.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership.
    :param notes: Optional freeform guidance for the planning agents.
    :param writing_samples: Example texts for style analysis.
    :param reference_urls: Optional URLs for the planning agents to use as research context.
    """

    topic: str
    audience: str
    notes: str = ""
    writing_samples: list[str] = []
    reference_urls: list[str] = []


@router.post("", status_code=201)
def create_session(body: CreateSessionRequest, store: SessionStore = Depends(get_store)) -> dict:
    """
    Create a new writing session and persist it.

    :param body: Topic, audience, and optional guidance fields.
    :param store: Injected session store.
    :returns: The newly created session as a dict.
    """
    session = WritingSession(
        topic=body.topic,
        audience=body.audience,
        notes=body.notes,
        writing_samples=body.writing_samples,
        reference_urls=body.reference_urls,
    )
    store.create(session)
    return asdict(session)


@router.get("/{session_id}")
def get_session(session_id: str, store: SessionStore = Depends(get_store)) -> dict:
    """
    Retrieve an existing writing session by ID.

    :param session_id: The UUID of the session to look up.
    :param store: Injected session store.
    :returns: The session as a dict.
    :raises HTTPException: 404 if the session does not exist.
    """
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return asdict(session)
