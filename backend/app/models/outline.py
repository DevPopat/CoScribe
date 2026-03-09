"""
Pydantic models for a writing outline and its individual sections.

An ``Outline`` is produced by the planning agents and holds the full
structure of the article before and during drafting. Each ``Section``
tracks its own draft content and approval state.
"""

from typing import Optional
from pydantic import BaseModel


class Section(BaseModel):
    """
    A single section within an outline.

    :param title: Heading for this section.
    :param key_points: Bullet points the draft should cover.
    :param draft: AI-generated draft text, populated during the drafting phase.
    :param approved: Whether the user has approved this section's draft.
    """

    title: str
    key_points: list[str]
    draft: Optional[str] = None
    approved: bool = False


class Outline(BaseModel):
    """
    The full article outline produced by the planning agents.

    :param title: Overall article title.
    :param brief: Short summary of the article's purpose and angle.
    :param tone_guidance: Style and tone instructions derived from the user's writing samples.
    :param sections: Ordered list of sections to be drafted.
    """

    title: str
    brief: str
    tone_guidance: str
    sections: list[Section]
