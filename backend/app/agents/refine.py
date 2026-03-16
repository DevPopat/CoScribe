"""
Refine agent — edits an existing outline based on user feedback.

Uses an agentic loop with web_search and fetch_url tools so the agent
can look up additional context when the user requests changes.  Returns
a JSON object containing the updated outline and a natural-language reply.
"""

import json

from app.agents.utils import FETCH_URL_TOOL, WEB_SEARCH_TOOL, run_agent_loop
from app.models.outline import Outline

_SYSTEM_PROMPT = (
    "You are an outline editor for a blog post. The user will show you the "
    "current outline and ask for changes. Apply the requested edits and return "
    "a JSON object with exactly two keys:\n"
    '  "outline" — the full updated outline matching this schema:\n'
    "    {\"title\": \"string\", \"brief\": \"string\", \"tone_guidance\": \"string\", "
    "\"sections\": [{\"title\": \"string\", \"key_points\": [\"string\"], \"sources\": [\"string\"]}]}\n"
    '  "reply" — a short natural-language summary of what you changed.\n\n'
    "Return only valid JSON with no markdown fences or extra text. "
    "Use the web_search and fetch_url tools if you need additional context "
    "to fulfil the user's request."
)


def refine_outline(
    current_outline: Outline,
    history: list[dict],
    message: str,
) -> tuple[Outline, str]:
    """
    Refine an outline based on user feedback.

    Passes the current outline and conversation history to the model along
    with the new user message.  The model returns an updated outline and
    a natural-language reply describing the changes.

    :param current_outline: The outline to modify.
    :param history: Previous refinement conversation turns.
    :param message: The latest user refinement request.
    :returns: A tuple of (updated Outline, assistant reply text).
    """
    context = (
        f"Current outline:\n{current_outline.model_dump_json(indent=2)}\n\n"
        f"User request: {message}"
    )

    messages = list(history) + [{"role": "user", "content": context}]

    raw = run_agent_loop(
        messages=messages,
        tools=[WEB_SEARCH_TOOL, FETCH_URL_TOOL],
        system=_SYSTEM_PROMPT,
    )

    parsed = json.loads(raw)
    updated_outline = Outline.model_validate(parsed["outline"])
    reply = parsed["reply"]
    return updated_outline, reply
