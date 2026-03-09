"""
Abstract base class for session persistence.

All concrete store implementations must satisfy this interface.
Keeping route handlers coupled only to ``SessionStore`` (not to any
concrete class) means the storage backend can be swapped without
touching API code.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.session import WritingSession


class SessionStore(ABC):
    """Abstract interface for reading and writing ``WritingSession`` objects."""

    @abstractmethod
    def create(self, session: WritingSession) -> None:
        """
        Persist a new session.

        :param session: The session to store. Must have a unique ``id``.
        """
        ...

    @abstractmethod
    def get(self, session_id: str) -> Optional[WritingSession]:
        """
        Retrieve a session by its ID.

        :param session_id: The UUID of the session to look up.
        :returns: The matching session, or ``None`` if not found.
        """
        ...

    @abstractmethod
    def update(self, session: WritingSession) -> None:
        """
        Overwrite an existing session with updated state.

        :param session: The session to update. Matched by ``session.id``.
        """
        ...
