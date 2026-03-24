"""
Section drafter agent — writes prose for a single outline section.

Makes a single call to claude-sonnet-4-6 using the outline context
(title, brief, tone guidance) and the section's key points.
"""

from app.agents.utils import anthropic_client as client


def draft_section(
    outline_title: str,
    brief: str,
    tone_guidance: str,
    section_title: str,
    key_points: list[str],
) -> str:
    """
    Draft the text for a single section of the article.

    :param outline_title: Overall article title for context.
    :param brief: Short summary of the article's purpose and angle.
    :param tone_guidance: Style and tone instructions.
    :param section_title: Heading of the section to draft.
    :param key_points: Bullet points the draft should cover.
    :returns: The drafted prose for this section.
    """
    points = "\n".join(f"- {p}" for p in key_points)
    prompt = (
        f"You are writing one section of a blog post.\n\n"
        f"Article title: {outline_title}\n"
        f"Article brief: {brief}\n"
        f"Tone: {tone_guidance}\n\n"
        f"Section: {section_title}\n"
        f"Key points to cover:\n{points}\n\n"
        f"Write the section as polished prose. Do not include the section "
        f"heading — just the body text."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
