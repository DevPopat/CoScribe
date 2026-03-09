"""
Tests for the session CRUD API endpoints (POST /sessions, GET /sessions/{id}).

Uses FastAPI's TestClient with the store monkeypatched to an isolated
MemorySessionStore so tests do not share state.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import deps
from app.store.memory import MemorySessionStore


@pytest.fixture(autouse=True)
def isolated_store():
    """Replace the global store with a fresh instance for each test."""
    deps._store = MemorySessionStore()
    yield
    deps._store = MemorySessionStore()


client = TestClient(app)


def test_create_session_returns_201():
    response = client.post("/sessions", json={"topic": "Baking bread", "audience": "Beginners"})
    assert response.status_code == 201


def test_create_session_returns_id_and_status():
    response = client.post("/sessions", json={"topic": "Baking bread", "audience": "Beginners"})
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"


def test_create_session_persists_topic_and_audience():
    response = client.post("/sessions", json={"topic": "Baking bread", "audience": "Beginners"})
    data = response.json()
    assert data["topic"] == "Baking bread"
    assert data["audience"] == "Beginners"


def test_get_session_returns_created_session():
    create = client.post("/sessions", json={"topic": "Rust async", "audience": "Intermediate devs"})
    session_id = create.json()["id"]

    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == session_id


def test_get_nonexistent_session_returns_404():
    response = client.get("/sessions/does-not-exist")
    assert response.status_code == 404
