"""
Research agent — gathers topic context and supporting points.

Uses an agentic loop with web_search and fetch_url tools so the agent can
actively look up current facts before summarising its findings. Runs on
Anthropic (uses the built-in web_search tool). Returns a structured dict
with a text summary and the list of URLs fetched during research so callers
can attribute sources to outline sections.
"""

import json
import logging
import re

from app.agents.utils import FETCH_URL_TOOL, WEB_SEARCH_TOOL, run_agent_loop

logger = logging.getLogger(__name__)

_RESPONSE_SCHEMA = """
{
  "summary": "string — concise summary of key facts, angles, and supporting points",
  "urls": ["string — every URL you fetched via fetch_url; empty list if none"]
}
"""

_SYSTEM_PROMPT = (
    "You are a research assistant helping plan a blog post/article. "
    "Use the web_search tool to find relevant, up-to-date information and the "
    "fetch_url tool to read specific pages when useful.\n\n"
    "When you have gathered enough context, respond with ONLY valid JSON — "
    "no markdown fences, no commentary, no extra text before or after. "
    "Your entire response must be a single JSON object matching this schema:\n"
    f"{_RESPONSE_SCHEMA}\n"
    "Do NOT include any text outside the JSON object."
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
    logger.info("[research] starting research_topic — topic=%s, audience=%s", topic, audience)
    raw = run_agent_loop(
        messages=[{"role": "user", "content": prompt}],
        tools=[WEB_SEARCH_TOOL, FETCH_URL_TOOL],
        system=_SYSTEM_PROMPT,
    )
    logger.info("[research] raw agent output (%d chars):\n%s", len(raw), raw)

    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw.strip())
    logger.debug("[research] after fence stripping (%d chars):\n%s", len(raw), raw)

    # The model sometimes wraps JSON in prose; extract the first { … } object.
    try:
        result = json.loads(raw)
        logger.info("[research] parsed JSON directly — keys=%s", list(result.keys()))
        return result
    except json.JSONDecodeError as exc:
        logger.warning("[research] json.loads failed: %s — attempting regex extraction", exc)
        logger.warning("[research] problematic raw text:\n%s", raw)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            logger.info("[research] regex extracted JSON (%d chars): %.500s", len(match.group()), match.group())
            return json.loads(match.group())
        # Last resort: return a best-effort summary with no URLs.
        logger.error("[research] no JSON found at all — using raw text as summary")
        return {"summary": raw, "urls": []}
