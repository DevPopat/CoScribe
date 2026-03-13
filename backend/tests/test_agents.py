"""
Tests for the four planning agents and the shared agentic loop.

All Anthropic API calls are mocked so tests run without a real API key
and execute fast. Each test verifies the agent returns the expected type
and passes its inputs through to the Claude call.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.refine import refine_outline
from app.agents.research import research_topic
from app.agents.style_analyzer import analyze_style
from app.agents.coverage_gap import find_gaps
from app.agents.synthesizer import synthesize_outline
from app.models.outline import Outline, Section


def make_end_turn_response(text: str) -> MagicMock:
    """Build a mock Anthropic response with stop_reason='end_turn'."""
    content_block = MagicMock()
    content_block.text = text
    content_block.type = "text"
    response = MagicMock()
    response.content = [content_block]
    response.stop_reason = "end_turn"
    return response


def make_tool_use_response(
    tool_name: str, tool_input: dict, tool_id: str = "tool_1"
) -> MagicMock:
    """Build a mock Anthropic response with stop_reason='tool_use'."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_id
    response = MagicMock()
    response.content = [tool_block]
    response.stop_reason = "tool_use"
    return response


# -- Research agent -----------------------------------------------------------


@patch("app.agents.research.run_agent_loop", return_value="Research findings about baking.")
def test_research_topic_returns_string(mock_loop):
    result = research_topic("How to bake bread", "Beginners", notes="Focus on sourdough")
    assert isinstance(result, str)
    assert len(result) > 0


@patch("app.agents.research.run_agent_loop", return_value="Some research.")
def test_research_topic_calls_loop(mock_loop):
    research_topic("How to bake bread", "Beginners")
    mock_loop.assert_called_once()


# -- Style analyzer -----------------------------------------------------------


@patch("app.agents.style_analyzer.run_agent_loop", return_value="Conversational and direct tone.")
def test_analyze_style_returns_string(mock_loop):
    result = analyze_style(["I love writing simple, clear prose.", "Keep it short."])
    assert isinstance(result, str)
    assert len(result) > 0


@patch("app.agents.style_analyzer.run_agent_loop", return_value="No samples provided; use neutral tone.")
def test_analyze_style_with_no_samples_returns_string(mock_loop):
    result = analyze_style([])
    assert isinstance(result, str)


@patch("app.agents.style_analyzer.run_agent_loop", return_value="Witty, informal voice with technical depth.")
def test_analyze_style_with_reference_urls_includes_fetch_tool(mock_loop):
    """When reference_urls are passed, FETCH_URL_TOOL should be included in tools."""
    analyze_style(
        writing_samples=["Short punchy paragraphs."],
        reference_urls=["https://example.com/post1"],
    )
    kwargs = mock_loop.call_args.kwargs
    tool_names = [t.get("name", "") for t in kwargs["tools"] if isinstance(t, dict)]
    assert "fetch_url" in tool_names


@patch("app.agents.style_analyzer.run_agent_loop", return_value="Neutral professional tone.")
def test_analyze_style_without_reference_urls_has_no_tools(mock_loop):
    """Without reference_urls, no tools should be provided."""
    analyze_style(writing_samples=["Clear and concise writing."])
    kwargs = mock_loop.call_args.kwargs
    assert kwargs["tools"] == []


# -- Coverage gap agent -------------------------------------------------------


@patch("app.agents.coverage_gap.client")
def test_find_gaps_returns_string(mock_client):
    mock_client.messages.create.return_value = make_end_turn_response(
        "Missing: beginner pitfalls, tools."
    )
    result = find_gaps(
        "How to bake bread", "Beginners", research="Some research", style="Direct tone"
    )
    assert isinstance(result, str)
    assert len(result) > 0


# -- Synthesizer agent --------------------------------------------------------


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
    mock_client.messages.create.return_value = make_end_turn_response(outline_json)
    result = synthesize_outline(
        topic="How to bake bread",
        audience="Beginners",
        research="Some research",
        style="Friendly tone",
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
    mock_client.messages.create.return_value = make_end_turn_response(outline_json)
    result = synthesize_outline(
        topic="Test", audience="All", research="r", style="s"
    )
    assert result.sections[0].key_points == ["Point A", "Point B"]


# -- Agent loop (multi-turn) --------------------------------------------------


@patch("app.agents.utils.client")
def test_run_agent_loop_single_turn(mock_client):
    """Loop with an immediate end_turn should return the text."""
    from app.agents.utils import run_agent_loop

    mock_client.messages.create.return_value = make_end_turn_response("Final answer.")
    result = run_agent_loop(
        messages=[{"role": "user", "content": "Hello"}],
        tools=[],
    )
    assert result == "Final answer."


@patch("app.agents.utils._fetch_url", return_value="Page content here.")
@patch("app.agents.utils.client")
def test_run_agent_loop_fetch_url_multi_turn(mock_client, mock_fetch):
    """Loop should handle a fetch_url tool call then return the final text."""
    from app.agents.utils import run_agent_loop

    tool_response = make_tool_use_response(
        "fetch_url", {"url": "https://example.com"}, tool_id="call_1"
    )
    final_response = make_end_turn_response("Summary based on fetched content.")
    mock_client.messages.create.side_effect = [tool_response, final_response]

    result = run_agent_loop(
        messages=[{"role": "user", "content": "Fetch this page"}],
        tools=[{"type": "custom", "name": "fetch_url", "input_schema": {}}],
    )
    assert result == "Summary based on fetched content."
    mock_fetch.assert_called_once_with("https://example.com")
    assert mock_client.messages.create.call_count == 2


@patch("app.agents.utils.client")
def test_run_agent_loop_unknown_tool_returns_empty(mock_client):
    """Unknown tool calls should get an empty result and the loop continues."""
    from app.agents.utils import run_agent_loop

    tool_response = make_tool_use_response(
        "web_search", {"query": "test"}, tool_id="call_1"
    )
    final_response = make_end_turn_response("Done searching.")
    mock_client.messages.create.side_effect = [tool_response, final_response]

    result = run_agent_loop(
        messages=[{"role": "user", "content": "Search for something"}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )
    assert result == "Done searching."
    assert mock_client.messages.create.call_count == 2


# -- Refine agent -------------------------------------------------------------


@patch("app.agents.refine.run_agent_loop")
def test_refine_outline_returns_updated_outline_and_reply(mock_loop):
    mock_loop.return_value = json.dumps({
        "outline": {
            "title": "Updated Title",
            "brief": "Updated brief",
            "tone_guidance": "Casual",
            "sections": [{"title": "New Intro", "key_points": ["Point 1"]}],
        },
        "reply": "I changed the title and restructured the intro.",
    })
    current = Outline(
        title="Original",
        brief="Original brief",
        tone_guidance="Formal",
        sections=[Section(title="Old Intro", key_points=["Old point"])],
    )

    updated, reply = refine_outline(current, [], "Make it more casual")

    assert isinstance(updated, Outline)
    assert updated.title == "Updated Title"
    assert reply == "I changed the title and restructured the intro."
    mock_loop.assert_called_once()
