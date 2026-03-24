"""
Synthesizer agent — combines all agent outputs into a single Outline.

Makes a single call to claude-sonnet-4-6 requesting a JSON response
that is parsed directly into an ``Outline`` Pydantic model.
"""

import json
import logging
import re
import time

import anthropic

from app.agents.utils import anthropic_client as client
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
        f"Return only valid JSON with no markdown fences or extra text."
    )
    logger.info("[synthesizer] starting — topic=%s, audience=%s", topic, audience)

    messages = [{"role": "user", "content": prompt}]

    for turn in range(3):
        for attempt in range(5):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=16384,
                    messages=messages,
                )
                break
            except anthropic.RateLimitError:
                wait = 15 * (2 ** attempt)
                logger.warning("[synthesizer] rate limited, attempt %d/5, retrying in %ds", attempt + 1, wait)
                if attempt == 4:
                    raise
                time.sleep(wait)

        logger.info("[synthesizer] turn %d — stop_reason=%s, content_blocks=%d", turn + 1, response.stop_reason, len(response.content))

        if response.stop_reason == "max_tokens":
            logger.warning("[synthesizer] turn %d — hit max_tokens, asking for shorter response", turn + 1)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": (
                    "Your response was cut off because it exceeded the token limit. "
                    "Please provide a shorter outline with fewer sections and more "
                    "concise key_points. Respond with ONLY the JSON."
                ),
            })
            continue

        # Got a complete response
        break

    raw = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            raw = block.text
            break

    logger.info("[synthesizer] raw output (%d chars): %.500s", len(raw), raw)

    if not raw:
        logger.error("[synthesizer] no text block in response")
        raise ValueError("Synthesizer returned no text")

    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw.strip())

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("[synthesizer] json.loads failed: %s — attempting regex extraction", exc)
        logger.warning("[synthesizer] problematic raw text:\n%s", raw)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            raise

    logger.info("[synthesizer] parsed outline — title=%s, sections=%d", parsed.get("title"), len(parsed.get("sections", [])))
    return Outline.model_validate(parsed)
