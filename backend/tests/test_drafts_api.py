"""
Tests for plan generation and refinement API endpoints.

All agent calls are mocked so tests run without an API key. Each test
creates a session via the CRUD endpoint first, then triggers plan
generation or refinement.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import deps
from app.models.outline import Outline, Section
from app.store.memory import MemorySessionStore


@pytest.fixture(autouse=True)
def isolated_store():
    """Replace the global store with a fresh instance for each test."""
    deps._store = MemorySessionStore()
    yield
    deps._store = MemorySessionStore()


client = TestClient(app)


def _create_session(**overrides) -> str:
    """Create a session and return its ID."""
    payload = {"topic": "Baking bread", "audience": "Beginners", **overrides}
    resp = client.post("/sessions", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _mock_outline() -> Outline:
    return Outline(
        title="How to Bake Bread",
        brief="A beginner guide.",
        tone_guidance="Friendly",
        sections=[Section(title="Intro", key_points=["Why bake?"])],
    )


@patch("app.api.drafts.synthesize_outline")
@patch("app.api.drafts.analyze_style", return_value="Friendly tone.")
@patch("app.api.drafts.research_topic", return_value="Research findings.")
def test_plan_returns_outline(mock_research, mock_style, mock_synth):
    mock_synth.return_value = _mock_outline()
    session_id = _create_session()

    resp = client.post(f"/sessions/{session_id}/plan")

    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "How to Bake Bread"
    assert len(data["sections"]) == 1


@patch("app.api.drafts.synthesize_outline")
@patch("app.api.drafts.analyze_style", return_value="Friendly tone.")
@patch("app.api.drafts.research_topic", return_value="Research findings.")
def test_plan_sets_session_status_to_outline_ready(mock_research, mock_style, mock_synth):
    mock_synth.return_value = _mock_outline()
    session_id = _create_session()

    client.post(f"/sessions/{session_id}/plan")

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["status"] == "outline_ready"


@patch("app.api.drafts.synthesize_outline")
@patch("app.api.drafts.analyze_style", return_value="Friendly tone.")
@patch("app.api.drafts.research_topic", return_value="Research findings.")
def test_plan_stores_outline_on_session(mock_research, mock_style, mock_synth):
    mock_synth.return_value = _mock_outline()
    session_id = _create_session()

    client.post(f"/sessions/{session_id}/plan")

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["title"] == "How to Bake Bread"


@patch("app.api.drafts.synthesize_outline")
@patch("app.api.drafts.analyze_style", return_value="Friendly tone.")
@patch("app.api.drafts.research_topic", return_value="Research findings.")
def test_plan_passes_session_fields_to_agents(mock_research, mock_style, mock_synth):
    mock_synth.return_value = _mock_outline()
    session_id = _create_session(
        notes="Focus on sourdough",
        writing_samples=["Keep it short."],
        reference_urls=["https://example.com"],
    )

    client.post(f"/sessions/{session_id}/plan")

    mock_research.assert_called_once_with("Baking bread", "Beginners", "Focus on sourdough")
    mock_style.assert_called_once_with(["Keep it short."], ["https://example.com"])
    mock_synth.assert_called_once_with(
        "Baking bread", "Beginners", "Research findings.", "Friendly tone."
    )


def test_plan_nonexistent_session_returns_404():
    resp = client.post("/sessions/does-not-exist/plan")
    assert resp.status_code == 404


# -- Refine endpoint ----------------------------------------------------------


def _mock_refined_outline() -> Outline:
    return Outline(
        title="How to Bake Sourdough",
        brief="A guide focused on sourdough.",
        tone_guidance="Friendly",
        sections=[
            Section(title="Intro", key_points=["Why sourdough?"]),
            Section(title="Starter", key_points=["How to make a starter"]),
        ],
    )


def _plan_session(session_id: str) -> None:
    """Run /plan on a session so it has an outline to refine."""
    with patch("app.api.drafts.synthesize_outline", return_value=_mock_outline()), \
         patch("app.api.drafts.analyze_style", return_value="Friendly tone."), \
         patch("app.api.drafts.research_topic", return_value="Research findings."):
        resp = client.post(f"/sessions/{session_id}/plan")
        assert resp.status_code == 200


@patch("app.api.drafts.refine_outline")
def test_refine_returns_outline_and_reply(mock_refine):
    mock_refine.return_value = (_mock_refined_outline(), "Added a sourdough starter section.")
    session_id = _create_session()
    _plan_session(session_id)

    resp = client.post(
        f"/sessions/{session_id}/plan/refine",
        json={"message": "Focus on sourdough specifically"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["outline"]["title"] == "How to Bake Sourdough"
    assert len(data["outline"]["sections"]) == 2
    assert data["reply"] == "Added a sourdough starter section."


@patch("app.api.drafts.refine_outline")
def test_refine_updates_session_outline(mock_refine):
    mock_refine.return_value = (_mock_refined_outline(), "Updated.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/plan/refine",
        json={"message": "Add sourdough section"},
    )

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["title"] == "How to Bake Sourdough"


@patch("app.api.drafts.refine_outline")
def test_refine_appends_to_history(mock_refine):
    mock_refine.return_value = (_mock_refined_outline(), "Done.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/plan/refine",
        json={"message": "Add more sections"},
    )

    session_resp = client.get(f"/sessions/{session_id}")
    history = session_resp.json()["refinement_history"]
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Add more sections"}
    assert history[1] == {"role": "assistant", "content": "Done."}


@patch("app.api.drafts.refine_outline")
def test_refine_keeps_status_outline_ready(mock_refine):
    mock_refine.return_value = (_mock_refined_outline(), "Updated.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/plan/refine",
        json={"message": "Change something"},
    )

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["status"] == "outline_ready"


def test_refine_nonexistent_session_returns_404():
    resp = client.post(
        "/sessions/does-not-exist/plan/refine",
        json={"message": "hello"},
    )
    assert resp.status_code == 404


def test_refine_without_outline_returns_400():
    session_id = _create_session()
    resp = client.post(
        f"/sessions/{session_id}/plan/refine",
        json={"message": "hello"},
    )
    assert resp.status_code == 400
