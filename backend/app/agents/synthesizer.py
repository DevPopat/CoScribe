"""
Synthesizer agent — combines all agent outputs into a single Outline.

Makes a single call to claude-sonnet-4-6 requesting a JSON response
that is parsed directly into an ``Outline`` Pydantic model.
"""

import json
import re
import time

import anthropic

from app.agents.utils import client
from app.models.outline import Outline

_OUTLINE_SCHEMA = """
{
  "title": "string",
  "brief": "string",
  "tone_guidance": "string",
  "sections": [
    {
      "title": "string",
      "key_points": ["string"]
    }
  ]
}
"""


def synthesize_outline(
    topic: str,
    audience: str,
    research: str,
    style: str,
) -> Outline:
    """
    Synthesize planning agent outputs into a structured article outline.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership.
    :param research: Output from the research agent.
    :param style: Output from the style analyzer agent.
    :returns: A fully populated ``Outline`` ready for section drafting.
    """
    prompt = (
        f"You are synthesizing a blog post outline.\n\n"
        f"Topic: {topic}\n"
        f"Audience: {audience}\n\n"
        f"Research:\n{research}\n\n"
        f"Writing style:\n{style}\n\n"
        f"Produce a structured outline as JSON matching this schema exactly:\n"
        f"{_OUTLINE_SCHEMA}\n\n"
        f"Return only valid JSON with no markdown fences or extra text."
    )
    for attempt in range(5):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except anthropic.RateLimitError:
            if attempt == 4:
                raise
            time.sleep(15 * (2 ** attempt))

    raw = response.content[0].text
    # Strip markdown fences the model may wrap around the JSON
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw.strip())
    return Outline.model_validate(json.loads(raw))
