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


@patch("app.agents.research.run_agent_loop", return_value=json.dumps({
    "summary": "Baking bread requires flour, water, yeast, and patience.",
    "urls": ["https://example.com/bread-guide"],
}))
def test_research_topic_returns_dict(mock_loop):
    result = research_topic("How to bake bread", "Beginners", notes="Focus on sourdough")
    assert isinstance(result, dict)
    assert "summary" in result
    assert "urls" in result


@patch("app.agents.research.run_agent_loop", return_value=json.dumps({
    "summary": "Key findings about baking.",
    "urls": ["https://example.com/a", "https://example.com/b"],
}))
def test_research_topic_returns_urls(mock_loop):
    result = research_topic("How to bake bread", "Beginners")
    assert result["urls"] == ["https://example.com/a", "https://example.com/b"]


@patch("app.agents.research.run_agent_loop", return_value=json.dumps({
    "summary": "Summary with no URLs.",
    "urls": [],
}))
def test_research_topic_returns_empty_urls_when_none_fetched(mock_loop):
    result = research_topic("How to bake bread", "Beginners")
    assert result["urls"] == []
    assert isinstance(result["summary"], str)


@patch("app.agents.research.run_agent_loop", return_value=(
    "```json\n" + json.dumps({"summary": "Bread facts.", "urls": []}) + "\n```"
))
def test_research_topic_strips_markdown_fences(mock_loop):
    result = research_topic("How to bake bread", "Beginners")
    assert result["summary"] == "Bread facts."


@patch("app.agents.research.run_agent_loop", return_value=json.dumps({
    "summary": "Research.", "urls": [],
}))
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
        "sections": [{"title": "Intro", "key_points": ["Point A", "Point B"], "sources": []}],
    })
    mock_client.messages.create.return_value = make_end_turn_response(outline_json)
    result = synthesize_outline(
        topic="Test", audience="All", research="r", style="s"
    )
    assert result.sections[0].key_points == ["Point A", "Point B"]


@patch("app.agents.synthesizer.client")
def test_synthesize_outline_sections_have_sources(mock_client):
    """Sources returned by the model are stored on each section."""
    outline_json = json.dumps({
        "title": "Test",
        "brief": "brief",
        "tone_guidance": "neutral",
        "sections": [
            {
                "title": "Intro",
                "key_points": ["Point A"],
                "sources": ["https://example.com/a", "https://example.com/b"],
            }
        ],
    })
    mock_client.messages.create.return_value = make_end_turn_response(outline_json)
    result = synthesize_outline(
        topic="Test", audience="All", research="r", style="s"
    )
    assert result.sections[0].sources == [
        "https://example.com/a",
        "https://example.com/b",
    ]


@patch("app.agents.synthesizer.client")
def test_synthesize_outline_includes_research_urls_in_prompt(mock_client):
    """research_urls are passed into the prompt when provided."""
    outline_json = json.dumps({
        "title": "T", "brief": "b", "tone_guidance": "n",
        "sections": [{"title": "S", "key_points": [], "sources": []}],
    })
    mock_client.messages.create.return_value = make_end_turn_response(outline_json)
    synthesize_outline(
        topic="Test",
        audience="All",
        research="r",
        style="s",
        research_urls=["https://source.com/1"],
    )
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "https://source.com/1" in prompt


@patch("app.agents.synthesizer.client")
def test_synthesize_outline_no_urls_prompt_unchanged(mock_client):
    """When research_urls is empty the prompt works without URL section."""
    outline_json = json.dumps({
        "title": "T", "brief": "b", "tone_guidance": "n",
        "sections": [{"title": "S", "key_points": [], "sources": []}],
    })
    mock_client.messages.create.return_value = make_end_turn_response(outline_json)
    result = synthesize_outline(
        topic="Test", audience="All", research="r", style="s"
    )
    assert isinstance(result, Outline)


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


# -- Intake agent -------------------------------------------------------------


@patch("app.agents.intake.client")
def test_intake_asks_for_samples_when_only_topic_and_audience_given(mock_client):
    """Even with topic and audience, agent should ask for writing samples before marking ready."""
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "reply": "Got it! Do you have any writing samples or previous articles I can use to match your style? Share URLs or paste text — or just say 'skip'.",
        "ready": False,
    }))
    from app.agents.intake import extract_session_params

    result = extract_session_params([
        {"role": "user", "content": "Write about remote work for engineering managers."}
    ])

    assert result["ready"] is False
    assert "extracted" not in result
    assert isinstance(result["reply"], str)


@patch("app.agents.intake.client")
def test_intake_ready_when_samples_provided(mock_client):
    """Returns ready=True once topic, audience, and writing samples are all present."""
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "reply": "Perfect, I have everything I need. Building your outline now!",
        "ready": True,
        "extracted": {
            "topic": "The future of remote work",
            "audience": "Engineering managers",
            "notes": "Focus on async communication",
            "writing_samples": [],
            "reference_urls": ["https://myblog.com/post-1"],
        },
    }))
    from app.agents.intake import extract_session_params

    result = extract_session_params([
        {"role": "user", "content": "Write about remote work for engineering managers."},
        {"role": "assistant", "content": "Do you have any writing samples?"},
        {"role": "user", "content": "Sure, here: https://myblog.com/post-1"},
    ])

    assert result["ready"] is True
    assert result["extracted"]["topic"] == "The future of remote work"
    assert result["extracted"]["reference_urls"] == ["https://myblog.com/post-1"]


@patch("app.agents.intake.client")
def test_intake_ready_when_user_skips_samples(mock_client):
    """Returns ready=True when user explicitly declines to provide writing samples."""
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "reply": "No problem, I'll work with a neutral style. Building your outline!",
        "ready": True,
        "extracted": {
            "topic": "Machine learning for beginners",
            "audience": "Students",
            "writing_samples": [],
            "reference_urls": [],
        },
    }))
    from app.agents.intake import extract_session_params

    result = extract_session_params([
        {"role": "user", "content": "Write about ML for students."},
        {"role": "assistant", "content": "Do you have any writing samples?"},
        {"role": "user", "content": "No, just skip that."},
    ])

    assert result["ready"] is True
    assert result["extracted"]["writing_samples"] == []
    assert result["extracted"]["reference_urls"] == []


@patch("app.agents.intake.client")
def test_intake_not_ready_when_missing_audience(mock_client):
    """Returns ready=False with a follow-up question when audience is missing."""
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "reply": "Who is the target audience for this piece?",
        "ready": False,
    }))
    from app.agents.intake import extract_session_params

    result = extract_session_params([
        {"role": "user", "content": "I want to write about machine learning."}
    ])

    assert result["ready"] is False
    assert "extracted" not in result
    assert isinstance(result["reply"], str)


@patch("app.agents.intake.client")
def test_intake_passes_full_conversation(mock_client):
    """Passes the full message history to the model."""
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "reply": "Got it!",
        "ready": True,
        "extracted": {"topic": "ML", "audience": "Students", "writing_samples": [], "reference_urls": []},
    }))
    from app.agents.intake import extract_session_params

    messages = [
        {"role": "user", "content": "I want to write about ML."},
        {"role": "assistant", "content": "Who is your audience?"},
        {"role": "user", "content": "University students."},
    ]
    extract_session_params(messages)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["messages"] == messages


@patch("app.agents.intake.client")
def test_intake_strips_markdown_fences(mock_client):
    """Handles model wrapping JSON in markdown fences."""
    mock_client.messages.create.return_value = make_end_turn_response(
        "```json\n" + json.dumps({"reply": "Hi", "ready": False}) + "\n```"
    )
    from app.agents.intake import extract_session_params

    result = extract_session_params([{"role": "user", "content": "Hello"}])
    assert result["ready"] is False


# -- Refine agent -------------------------------------------------------------


@patch("app.agents.refine.run_agent_loop")
def test_refine_outline_returns_updated_outline_and_reply(mock_loop):
    mock_loop.return_value = json.dumps({
        "outline": {
            "title": "Updated Title",
            "brief": "Updated brief",
            "tone_guidance": "Casual",
            "sections": [{"title": "New Intro", "key_points": ["Point 1"], "sources": []}],
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


@patch("app.agents.refine.run_agent_loop")
def test_refine_outline_preserves_sources(mock_loop):
    """Sources on sections are preserved when the refine agent returns them."""
    mock_loop.return_value = json.dumps({
        "outline": {
            "title": "T", "brief": "b", "tone_guidance": "n",
            "sections": [{"title": "S", "key_points": [], "sources": ["https://src.com"]}],
        },
        "reply": "Done.",
    })
    current = Outline(
        title="T", brief="b", tone_guidance="n",
        sections=[Section(title="S", key_points=[], sources=["https://src.com"])],
    )
    updated, _ = refine_outline(current, [], "tweak it")
    assert updated.sections[0].sources == ["https://src.com"]


def test_refine_system_prompt_includes_sources_schema():
    """The refine agent's system prompt should mention sources in the schema."""
    from app.agents.refine import _SYSTEM_PROMPT
    assert "sources" in _SYSTEM_PROMPT


# -- Section refine agent -----------------------------------------------------


@patch("app.agents.section_refine.client")
def test_refine_section_returns_updated_draft_and_reply(mock_client):
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "draft": "Refined draft text.",
        "key_points": None,
        "sources": None,
        "reply": "Tightened the prose.",
    }))
    from app.agents.section_refine import refine_section

    draft, key_points, sources, reply = refine_section(
        outline_title="How to Bake Bread",
        brief="A beginner guide.",
        tone_guidance="Friendly",
        section_title="Intro",
        key_points=["Why bake?"],
        sources=[],
        current_draft="Long original draft.",
        message="Make it shorter",
    )

    assert draft == "Refined draft text."
    assert key_points is None
    assert sources is None
    assert reply == "Tightened the prose."


@patch("app.agents.section_refine.client")
def test_refine_section_returns_updated_key_points_and_sources(mock_client):
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "draft": "Updated draft.",
        "key_points": ["Point A", "Point B"],
        "sources": ["https://example.com"],
        "reply": "Added new angle and source.",
    }))
    from app.agents.section_refine import refine_section

    draft, key_points, sources, reply = refine_section(
        outline_title="T", brief="b", tone_guidance="n",
        section_title="S", key_points=["Old point"], sources=[],
        current_draft="Draft.", message="Expand and cite a source",
    )

    assert key_points == ["Point A", "Point B"]
    assert sources == ["https://example.com"]


@patch("app.agents.section_refine.client")
def test_refine_section_passes_context_in_prompt(mock_client):
    mock_client.messages.create.return_value = make_end_turn_response(json.dumps({
        "draft": "d", "key_points": None, "sources": None, "reply": "r",
    }))
    from app.agents.section_refine import refine_section

    refine_section(
        outline_title="Bread Guide",
        brief="Beginners welcome.",
        tone_guidance="Conversational",
        section_title="Mixing",
        key_points=["Combine flour and water"],
        sources=["https://baking.com"],
        current_draft="Mix the ingredients.",
        message="Be more specific",
    )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    prompt = call_kwargs["messages"][0]["content"]
    assert "Bread Guide" in prompt
    assert "Mixing" in prompt
    assert "Mix the ingredients." in prompt
    assert "Be more specific" in prompt
