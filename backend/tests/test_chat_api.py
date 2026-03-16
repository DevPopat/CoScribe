"""
Tests for the POST /chat endpoint.

All intake agent calls are mocked so tests run without an API key.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _post_chat(messages: list) -> dict:
    resp = client.post("/chat", json={"messages": messages})
    return resp


# -- Basic response shape -----------------------------------------------------


@patch("app.api.chat.extract_session_params", return_value={
    "reply": "Who is your target audience?",
    "ready": False,
})
def test_chat_returns_reply_and_ready(mock_extract):
    resp = _post_chat([{"role": "user", "content": "I want to write about AI."}])
    assert resp.status_code == 200
    data = resp.json()
    assert data["reply"] == "Who is your target audience?"
    assert data["ready"] is False


@patch("app.api.chat.extract_session_params", return_value={
    "reply": "Great, building your outline!",
    "ready": True,
    "extracted": {
        "topic": "AI trends",
        "audience": "Tech leaders",
        "writing_samples": [],
        "reference_urls": [],
    },
})
def test_chat_returns_extracted_fields_when_ready(mock_extract):
    resp = _post_chat([
        {"role": "user", "content": "Write about AI for tech leaders."},
        {"role": "assistant", "content": "Any writing samples?"},
        {"role": "user", "content": "No, skip."},
    ])
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["extracted"]["topic"] == "AI trends"
    assert data["extracted"]["audience"] == "Tech leaders"


@patch("app.api.chat.extract_session_params", return_value={
    "reply": "What topic?",
    "ready": False,
})
def test_chat_no_extracted_key_when_not_ready(mock_extract):
    resp = _post_chat([{"role": "user", "content": "Hello"}])
    assert resp.status_code == 200
    assert "extracted" not in resp.json()


# -- Input validation ---------------------------------------------------------


def test_chat_returns_422_when_messages_missing():
    resp = client.post("/chat", json={})
    assert resp.status_code == 422


def test_chat_returns_422_when_messages_empty():
    resp = client.post("/chat", json={"messages": []})
    assert resp.status_code == 422


# -- Agent is called correctly ------------------------------------------------


@patch("app.api.chat.extract_session_params", return_value={
    "reply": "Got it.",
    "ready": False,
})
def test_chat_passes_messages_to_agent(mock_extract):
    messages = [
        {"role": "user", "content": "Write about space exploration."},
        {"role": "assistant", "content": "Who is your audience?"},
        {"role": "user", "content": "Curious teenagers."},
    ]
    _post_chat(messages)
    mock_extract.assert_called_once_with(messages)
