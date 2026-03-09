from app.store.base import SessionStore
from app.store.memory import MemorySessionStore

_store: SessionStore = MemorySessionStore()


def get_store() -> SessionStore:
    return _store
