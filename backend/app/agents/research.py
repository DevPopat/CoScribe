"""
Research agent — gathers topic context and supporting points.

Makes a single call to claude-sonnet-4-6 and returns the raw text
response for use by downstream agents.
"""

import anthropic

client = anthropic.Anthropic()


def research_topic(topic: str, audience: str, notes: str = "") -> str:
    """
    Generate research findings for a given topic and target audience.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership.
    :param notes: Optional freeform guidance from the user.
    :returns: A text summary of relevant facts, angles, and supporting points.
    """
    prompt = (
        f"You are a research assistant helping plan a blog post.\n\n"
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Additional notes: {notes or 'None'}\n\n"
        f"Provide useful research findings, key facts, and supporting points "
        f"that would strengthen an article on this topic. Be concise and specific."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
