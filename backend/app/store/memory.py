"""
In-memory implementation of SessionStore.

Stores sessions in a plain Python dict. All data is lost when the
process restarts. Intended for the MVP only — replace with a
database-backed store for production persistence.
"""

from typing import Optional

from app.models.session import WritingSession
from app.store.base import SessionStore


class MemorySessionStore(SessionStore):
    """Dict-backed session store for local development and testing."""

    def __init__(self):
        self._store: dict[str, WritingSession] = {}

    def create(self, session: WritingSession) -> None:
        """
        Persist a new session in memory.

        :param session: The session to store.
        """
        self._store[session.id] = session

    def get(self, session_id: str) -> Optional[WritingSession]:
        """
        Retrieve a session by its ID.

        :param session_id: The UUID of the session to look up.
        :returns: The matching session, or ``None`` if not found.
        """
        return self._store.get(session_id)

    def update(self, session: WritingSession) -> None:
        """
        Overwrite an existing session with updated state.

        :param session: The session to update. Matched by ``session.id``.
        """
        self._store[session.id] = session
