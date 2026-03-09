"""
Coverage gap agent — finds missing angles and likely reader questions.

Takes the research and style outputs from earlier agents and identifies
what the article should also address to feel complete.
"""

import anthropic

client = anthropic.Anthropic()


def find_gaps(topic: str, audience: str, research: str, style: str) -> str:
    """
    Identify coverage gaps and unanswered reader questions for an article.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership.
    :param research: Output from the research agent.
    :param style: Output from the style analyzer agent.
    :returns: A list of missing angles, questions, or subtopics to include.
    """
    prompt = (
        f"You are helping plan a blog post.\n\n"
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Research so far:\n{research}\n\n"
        f"Writing style:\n{style}\n\n"
        f"What important angles, subtopics, or reader questions are missing "
        f"from the research above? List them concisely."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
