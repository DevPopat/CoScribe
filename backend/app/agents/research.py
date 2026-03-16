"""
Research agent — gathers topic context and supporting points.

Uses an agentic loop with web_search and fetch_url tools so the agent can
actively look up current facts before summarising its findings. Returns a
structured dict with a text summary and the list of URLs fetched during
research so callers can attribute sources to outline sections.
"""

import json
import re

from app.agents.utils import FETCH_URL_TOOL, WEB_SEARCH_TOOL, run_agent_loop

_SYSTEM_PROMPT = (
    "You are a research assistant helping plan write a blog post/article. "
    "Use the web_search tool to find relevant, up-to-date information and the "
    "fetch_url tool to read specific pages when useful. "
    "After gathering enough context, respond with valid JSON in this exact format "
    "(no markdown fences, no extra text):\n"
    '{"summary": "<concise summary of key facts, angles, and supporting points>", '
    '"urls": ["<url1>", "<url2>"]}\n'
    "The urls list should contain every URL you fetched via fetch_url. "
    "If you fetched no URLs, use an empty list."
)


def research_topic(topic: str, audience: str, notes: str = "") -> dict:
    """
    Generate research findings for a given topic and target audience.

    Runs an agentic loop that may invoke web_search and fetch_url before
    producing its final structured response.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership.
    :param notes: Optional freeform guidance from the user.
    :returns: A dict with ``summary`` (str) and ``urls`` (list[str]).
    """
    prompt = (
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Additional notes: {notes or 'None'}\n\n"
        f"Research this topic and provide useful findings, key facts, and "
        f"supporting points for an article targeting this audience."
    )
    raw = run_agent_loop(
        messages=[{"role": "user", "content": prompt}],
        tools=[WEB_SEARCH_TOOL, FETCH_URL_TOOL],
        system=_SYSTEM_PROMPT,
    )
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw.strip())
    return json.loads(raw)
