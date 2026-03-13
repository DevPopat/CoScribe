"""
Research agent — gathers topic context and supporting points.

Uses an agentic loop with web_search and fetch_url tools so the agent can
actively look up current facts before summarising its findings.
"""

from app.agents.utils import FETCH_URL_TOOL, WEB_SEARCH_TOOL, run_agent_loop

_SYSTEM_PROMPT = (
    "You are a research assistant helping plan write a blog post/article. "
    "Use the web_search tool to find relevant, up-to-date information and the "
    "fetch_url tool to read specific pages when useful. "
    "After gathering enough context, provide a concise summary of key facts, "
    "angles, and supporting points that would strengthen an article on the topic."
)


def research_topic(topic: str, audience: str, notes: str = "") -> str:
    """
    Generate research findings for a given topic and target audience.

    Runs an agentic loop that may invoke web_search and fetch_url before
    producing its final text summary.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership.
    :param notes: Optional freeform guidance from the user.
    :returns: A text summary of relevant facts, angles, and supporting points.
    """
    prompt = (
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Additional notes: {notes or 'None'}\n\n"
        f"Research this topic and provide useful findings, key facts, and "
        f"supporting points for an article targeting this audience."
    )
    return run_agent_loop(
        messages=[{"role": "user", "content": prompt}],
        tools=[WEB_SEARCH_TOOL, FETCH_URL_TOOL],
        system=_SYSTEM_PROMPT,
    )
