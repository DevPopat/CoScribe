from typing import Optional

from app.models.session import WritingSession
from app.store.base import SessionStore


class MemorySessionStore(SessionStore):
    def __init__(self):
        self._store: dict[str, WritingSession] = {}

    def create(self, session: WritingSession) -> None:
        self._store[session.id] = session

    def get(self, session_id: str) -> Optional[WritingSession]:
        return self._store.get(session_id)

    def update(self, session: WritingSession) -> None:
        self._store[session.id] = session
