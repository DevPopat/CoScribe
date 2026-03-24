"""
Synthesizer agent — combines all agent outputs into a single Outline.

Runs on OpenAI (gpt-4o-search-preview) to avoid sharing the Anthropic
rate-limit pool with the research agent. Makes a single call requesting
a JSON response that is parsed into an ``Outline`` Pydantic model.
"""

import json
import logging
import re

from app.agents.utils import run_agent_loop, safe_json_loads
from app.models.outline import Outline

logger = logging.getLogger(__name__)

_OUTLINE_SCHEMA = """
{
  "title": "string",
  "brief": "string",
  "tone_guidance": "string",
  "sections": [
    {
      "title": "string",
      "key_points": ["string"],
      "sources": ["string"]
    }
  ]
}
"""


def synthesize_outline(
    topic: str,
    audience: str,
    research: str,
    style: str,
    research_urls: list[str] | None = None,
) -> Outline:
    """
    Synthesize planning agent outputs into a structured article outline.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership.
    :param research: Output from the research agent.
    :param style: Output from the style analyzer agent.
    :param research_urls: URLs fetched during research to distribute across sections.
    :returns: A fully populated ``Outline`` ready for section drafting.
    """
    urls_block = ""
    if research_urls:
        urls_list = "\n".join(f"  - {u}" for u in research_urls)
        urls_block = (
            f"\nResearch sources (distribute relevant URLs into each section's "
            f"\"sources\" list):\n{urls_list}\n"
        )

    prompt = (
        f"You are synthesizing a blog post outline.\n\n"
        f"Topic: {topic}\n"
        f"Audience: {audience}\n\n"
        f"Research:\n{research}\n"
        f"{urls_block}\n"
        f"Writing style:\n{style}\n\n"
        f"Produce a structured outline as JSON matching this schema exactly:\n"
        f"{_OUTLINE_SCHEMA}\n\n"
        f"Return ONLY valid JSON with no markdown fences or extra text. "
        f"Do NOT include any text outside the JSON object."
    )
    logger.info("[synthesizer] starting — topic=%s, audience=%s", topic, audience)

    raw = run_agent_loop(
        messages=[{"role": "user", "content": prompt}],
        tools=[],
        system="You produce structured article outlines as JSON. Respond with ONLY valid JSON.",
        provider="openai",
    )

    logger.info("[synthesizer] raw output (%d chars): %.500s", len(raw), raw)

    if not raw:
        logger.error("[synthesizer] empty response")
        raise ValueError("Synthesizer returned no text")

    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw.strip())

    try:
        parsed = safe_json_loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("[synthesizer] json.loads failed: %s — attempting regex extraction", exc)
        logger.warning("[synthesizer] problematic raw text:\n%s", raw)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            parsed = safe_json_loads(match.group())
        else:
            raise

    logger.info("[synthesizer] parsed outline — title=%s, sections=%d", parsed.get("title"), len(parsed.get("sections", [])))
    return Outline.model_validate(parsed)
