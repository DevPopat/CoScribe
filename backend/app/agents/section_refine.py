"""
Section refine agent — edits a drafted section based on user feedback.

Makes a single call to claude-sonnet-4-6 with the section context, current
draft, and user feedback, returning an updated draft and a natural-language
reply describing the changes.  Optionally returns updated key_points and
sources if the agent decides to revise them.
"""

import json
from typing import Optional

from app.agents.utils import anthropic_client as client

_SYSTEM_PROMPT = (
    "You are a section editor for a blog post. The user will show you a "
    "drafted section and ask for specific changes. Apply the feedback and "
    "return a JSON object with exactly these keys:\n"
    '  "draft" — the full updated section text (required)\n'
    '  "key_points" — updated list of bullet-point strings if they changed, '
    "or null if unchanged\n"
    '  "sources" — updated list of source URL strings if they changed, '
    "or null if unchanged\n"
    '  "reply" — a short natural-language summary of what you changed.\n\n'
    "Return only valid JSON with no markdown fences or extra text."
)


def refine_section(
    outline_title: str,
    brief: str,
    tone_guidance: str,
    section_title: str,
    key_points: list[str],
    sources: list[str],
    current_draft: str,
    message: str,
) -> tuple[str, Optional[list[str]], Optional[list[str]], str]:
    """
    Refine a drafted section based on user feedback.

    :param outline_title: Overall article title for context.
    :param brief: Short summary of the article's purpose and angle.
    :param tone_guidance: Style and tone instructions.
    :param section_title: Heading of the section being refined.
    :param key_points: Current key points for this section.
    :param sources: Current source URLs for this section.
    :param current_draft: The existing draft text to refine.
    :param message: The user's feedback or refinement instruction.
    :returns: A tuple of (updated_draft, updated_key_points, updated_sources, reply).
        ``updated_key_points`` and ``updated_sources`` are ``None`` if unchanged.
    """
    points = "\n".join(f"- {p}" for p in key_points)
    sources_str = "\n".join(f"- {s}" for s in sources) if sources else "(none)"

    prompt = (
        f"Article title: {outline_title}\n"
        f"Brief: {brief}\n"
        f"Tone: {tone_guidance}\n\n"
        f"Section: {section_title}\n"
        f"Key points:\n{points}\n"
        f"Sources:\n{sources_str}\n\n"
        f"Current draft:\n{current_draft}\n\n"
        f"User feedback: {message}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    parsed = json.loads(response.content[0].text)
    return (
        parsed["draft"],
        parsed.get("key_points"),
        parsed.get("sources"),
        parsed["reply"],
    )
