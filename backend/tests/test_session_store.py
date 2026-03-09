import pytest
from app.models.session import WritingSession, SessionStatus
from app.store.memory import MemorySessionStore


@pytest.fixture
def store():
    return MemorySessionStore()


def test_create_and_get_session(store):
    session = WritingSession(topic="How to bake bread", audience="Beginners")
    store.create(session)
    retrieved = store.get(session.id)
    assert retrieved == session


def test_get_nonexistent_session_returns_none(store):
    assert store.get("nonexistent-id") is None


def test_update_session(store):
    session = WritingSession(topic="How to bake bread", audience="Beginners")
    store.create(session)
    session.status = SessionStatus.PLANNING
    store.update(session)
    assert store.get(session.id).status == SessionStatus.PLANNING


def test_create_session_has_default_status(store):
    session = WritingSession(topic="Test", audience="All")
    assert session.status == SessionStatus.PENDING


def test_sessions_are_isolated(store):
    s1 = WritingSession(topic="Topic A", audience="Audience A")
    s2 = WritingSession(topic="Topic B", audience="Audience B")
    store.create(s1)
    store.create(s2)
    assert store.get(s1.id).topic == "Topic A"
    assert store.get(s2.id).topic == "Topic B"
