"""
Dependency injection providers for FastAPI route handlers.

The active store is instantiated once at module load time. To swap
to a persistent store, change the assignment of ``_store`` to any
other ``SessionStore`` implementation — no route code needs to change.
"""

from app.store.base import SessionStore
from app.store.memory import MemorySessionStore

# MVP: in-memory store. Replace with a persistent implementation when needed.
_store: SessionStore = MemorySessionStore()


def get_store() -> SessionStore:
    """
    Return the active session store instance.

    Intended for use as a FastAPI dependency via ``Depends(get_store)``.

    :returns: The application-wide session store.
    """
    return _store
