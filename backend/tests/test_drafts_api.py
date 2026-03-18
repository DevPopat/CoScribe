"""
Tests for plan generation, refinement, section draft, and approve API endpoints.

All agent calls are mocked so tests run without an API key. Each test
creates a session via the CRUD endpoint first, then triggers the relevant
endpoint.
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


# -- Section draft endpoint ---------------------------------------------------


@patch("app.api.drafts.draft_section", return_value="Baking bread is a joy.")
def test_draft_returns_text(mock_draft):
    session_id = _create_session()
    _plan_session(session_id)

    resp = client.post(f"/sessions/{session_id}/sections/0/draft")

    assert resp.status_code == 200
    assert resp.json()["draft"] == "Baking bread is a joy."


@patch("app.api.drafts.draft_section", return_value="Draft text.")
def test_draft_stores_on_section(mock_draft):
    session_id = _create_session()
    _plan_session(session_id)

    client.post(f"/sessions/{session_id}/sections/0/draft")

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["sections"][0]["draft"] == "Draft text."


@patch("app.api.drafts.draft_section", return_value="Draft text.")
def test_draft_sets_status_to_drafting(mock_draft):
    session_id = _create_session()
    _plan_session(session_id)

    client.post(f"/sessions/{session_id}/sections/0/draft")

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["status"] == "drafting"


@patch("app.api.drafts.draft_section", return_value="Draft text.")
def test_draft_passes_outline_context(mock_draft):
    session_id = _create_session()
    _plan_session(session_id)

    client.post(f"/sessions/{session_id}/sections/0/draft")

    mock_draft.assert_called_once_with(
        "How to Bake Bread", "A beginner guide.", "Friendly", "Intro", ["Why bake?"]
    )


def test_draft_nonexistent_session_returns_404():
    resp = client.post("/sessions/does-not-exist/sections/0/draft")
    assert resp.status_code == 404


def test_draft_without_outline_returns_400():
    session_id = _create_session()
    resp = client.post(f"/sessions/{session_id}/sections/0/draft")
    assert resp.status_code == 400


def test_draft_out_of_range_section_returns_404():
    session_id = _create_session()
    _plan_session(session_id)
    resp = client.post(f"/sessions/{session_id}/sections/99/draft")
    assert resp.status_code == 404


# -- Section approve endpoint -------------------------------------------------


@patch("app.api.drafts.draft_section", return_value="Draft text.")
def test_approve_marks_section_approved(mock_draft):
    session_id = _create_session()
    _plan_session(session_id)
    client.post(f"/sessions/{session_id}/sections/0/draft")

    resp = client.post(f"/sessions/{session_id}/sections/0/approve")

    assert resp.status_code == 200
    assert resp.json()["approved"] is True
    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["sections"][0]["approved"] is True


@patch("app.api.drafts.draft_section", return_value="Draft text.")
def test_approve_with_edited_text_replaces_draft(mock_draft):
    session_id = _create_session()
    _plan_session(session_id)
    client.post(f"/sessions/{session_id}/sections/0/draft")

    resp = client.post(
        f"/sessions/{session_id}/sections/0/approve",
        json={"text": "My edited version."},
    )

    assert resp.status_code == 200
    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["sections"][0]["draft"] == "My edited version."


def test_approve_with_text_but_no_prior_draft():
    """Approve with user-supplied text should work even without a prior draft."""
    session_id = _create_session()
    _plan_session(session_id)

    resp = client.post(
        f"/sessions/{session_id}/sections/0/approve",
        json={"text": "User-written section."},
    )

    assert resp.status_code == 200
    session_resp = client.get(f"/sessions/{session_id}")
    section = session_resp.json()["outline"]["sections"][0]
    assert section["draft"] == "User-written section."
    assert section["approved"] is True


def test_approve_without_draft_or_text_returns_400():
    session_id = _create_session()
    _plan_session(session_id)
    resp = client.post(f"/sessions/{session_id}/sections/0/approve")
    assert resp.status_code == 400


@patch("app.api.drafts.draft_section", return_value="Draft text.")
def test_approve_all_sections_sets_status_complete(mock_draft):
    """When all sections are approved, session status becomes complete."""
    session_id = _create_session()
    _plan_session(session_id)
    client.post(f"/sessions/{session_id}/sections/0/draft")
    client.post(f"/sessions/{session_id}/sections/0/approve")

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["status"] == "complete"


# -- Section refine endpoint --------------------------------------------------


@patch("app.api.drafts.refine_section")
def test_section_refine_returns_draft_and_reply(mock_refine):
    mock_refine.return_value = ("Refined draft.", None, None, "Tightened the intro.")
    session_id = _create_session()
    _plan_session(session_id)

    resp = client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "Make it shorter", "current_draft": "Long draft text."},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["draft"] == "Refined draft."
    assert data["reply"] == "Tightened the intro."


@patch("app.api.drafts.refine_section")
def test_section_refine_stores_updated_draft_on_section(mock_refine):
    mock_refine.return_value = ("Refined draft.", None, None, "Done.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "Be concise", "current_draft": "Original."},
    )

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["sections"][0]["draft"] == "Refined draft."


@patch("app.api.drafts.refine_section")
def test_section_refine_updates_key_points_when_agent_returns_them(mock_refine):
    mock_refine.return_value = ("Draft.", ["New point A", "New point B"], None, "Updated points.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "Add a new angle", "current_draft": "Draft."},
    )

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["sections"][0]["key_points"] == [
        "New point A",
        "New point B",
    ]


@patch("app.api.drafts.refine_section")
def test_section_refine_keeps_key_points_when_agent_returns_none(mock_refine):
    mock_refine.return_value = ("Draft.", None, None, "Just rewrote prose.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "Fix grammar", "current_draft": "Draft."},
    )

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["sections"][0]["key_points"] == ["Why bake?"]


@patch("app.api.drafts.refine_section")
def test_section_refine_updates_sources_when_agent_returns_them(mock_refine):
    mock_refine.return_value = ("Draft.", None, ["https://example.com"], "Added source.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "Add a citation", "current_draft": "Draft."},
    )

    session_resp = client.get(f"/sessions/{session_id}")
    assert session_resp.json()["outline"]["sections"][0]["sources"] == ["https://example.com"]


@patch("app.api.drafts.refine_section")
def test_section_refine_passes_correct_context_to_agent(mock_refine):
    mock_refine.return_value = ("Draft.", None, None, "Done.")
    session_id = _create_session()
    _plan_session(session_id)

    client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "Be more vivid", "current_draft": "Original draft."},
    )

    mock_refine.assert_called_once_with(
        "How to Bake Bread",
        "A beginner guide.",
        "Friendly",
        "Intro",
        ["Why bake?"],
        [],
        "Original draft.",
        "Be more vivid",
    )


@patch("app.api.drafts.refine_section")
def test_section_refine_returns_key_points_and_sources_in_response(mock_refine):
    mock_refine.return_value = ("Draft.", ["Point A"], ["https://src.com"], "Updated.")
    session_id = _create_session()
    _plan_session(session_id)

    resp = client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "Expand", "current_draft": "Draft."},
    )

    data = resp.json()
    assert data["key_points"] == ["Point A"]
    assert data["sources"] == ["https://src.com"]


def test_section_refine_nonexistent_session_returns_404():
    resp = client.post(
        "/sessions/does-not-exist/sections/0/refine",
        json={"message": "hi", "current_draft": "x"},
    )
    assert resp.status_code == 404


def test_section_refine_without_outline_returns_400():
    session_id = _create_session()
    resp = client.post(
        f"/sessions/{session_id}/sections/0/refine",
        json={"message": "hi", "current_draft": "x"},
    )
    assert resp.status_code == 400


def test_section_refine_out_of_range_section_returns_404():
    session_id = _create_session()
    _plan_session(session_id)
    resp = client.post(
        f"/sessions/{session_id}/sections/99/refine",
        json={"message": "hi", "current_draft": "x"},
    )
    assert resp.status_code == 404
