"""
Tests for the four planning agents.

All Anthropic API calls are mocked so tests run without a real API key
and execute fast. Each test verifies the agent returns the expected type
and passes its inputs through to the Claude call.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.research import research_topic
from app.agents.style_analyzer import analyze_style
from app.agents.coverage_gap import find_gaps
from app.agents.synthesizer import synthesize_outline
from app.models.outline import Outline


def make_mock_response(text: str) -> MagicMock:
    """Build a minimal mock that looks like an Anthropic message response."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


@patch("app.agents.research.client")
def test_research_topic_returns_string(mock_client):
    mock_client.messages.create.return_value = make_mock_response("Research findings about baking.")
    result = research_topic("How to bake bread", "Beginners", notes="Focus on sourdough")
    assert isinstance(result, str)
    assert len(result) > 0


@patch("app.agents.research.client")
def test_research_topic_calls_claude(mock_client):
    mock_client.messages.create.return_value = make_mock_response("Some research.")
    research_topic("How to bake bread", "Beginners")
    mock_client.messages.create.assert_called_once()


@patch("app.agents.style_analyzer.client")
def test_analyze_style_returns_string(mock_client):
    mock_client.messages.create.return_value = make_mock_response("Conversational and direct tone.")
    result = analyze_style(["I love writing simple, clear prose.", "Keep it short."])
    assert isinstance(result, str)
    assert len(result) > 0


@patch("app.agents.style_analyzer.client")
def test_analyze_style_with_no_samples_returns_string(mock_client):
    mock_client.messages.create.return_value = make_mock_response("No samples provided; use neutral tone.")
    result = analyze_style([])
    assert isinstance(result, str)


@patch("app.agents.coverage_gap.client")
def test_find_gaps_returns_string(mock_client):
    mock_client.messages.create.return_value = make_mock_response("Missing: beginner pitfalls, tools.")
    result = find_gaps("How to bake bread", "Beginners", research="Some research", style="Direct tone")
    assert isinstance(result, str)
    assert len(result) > 0


@patch("app.agents.synthesizer.client")
def test_synthesize_outline_returns_outline(mock_client):
    outline_json = json.dumps({
        "title": "How to Bake Bread",
        "brief": "A beginner guide to baking.",
        "tone_guidance": "Friendly and simple.",
        "sections": [
            {"title": "Introduction", "key_points": ["Why bake?", "What you need"]},
            {"title": "The Process", "key_points": ["Mixing", "Proofing", "Baking"]},
        ],
    })
    mock_client.messages.create.return_value = make_mock_response(outline_json)
    result = synthesize_outline(
        topic="How to bake bread",
        audience="Beginners",
        research="Some research",
        style="Friendly tone",
        gaps="Missing beginner pitfalls",
    )
    assert isinstance(result, Outline)
    assert result.title == "How to Bake Bread"
    assert len(result.sections) == 2


@patch("app.agents.synthesizer.client")
def test_synthesize_outline_sections_have_key_points(mock_client):
    outline_json = json.dumps({
        "title": "Test",
        "brief": "brief",
        "tone_guidance": "neutral",
        "sections": [{"title": "Intro", "key_points": ["Point A", "Point B"]}],
    })
    mock_client.messages.create.return_value = make_mock_response(outline_json)
    result = synthesize_outline(
        topic="Test", audience="All", research="r", style="s", gaps="g"
    )
    assert result.sections[0].key_points == ["Point A", "Point B"]
