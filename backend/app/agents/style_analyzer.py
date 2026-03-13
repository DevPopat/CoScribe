"""
Style analyzer agent — learns tone and writing preferences from user samples.

When reference_urls are provided the agent runs an agentic loop with
FETCH_URL_TOOL so it can read those pages alongside the raw writing samples.
When no URLs are given a single call (tools=[]) is made instead.
"""

from app.agents.utils import FETCH_URL_TOOL, run_agent_loop

_SYSTEM_PROMPT = (
    "You are a writing style analyst. Your job is to study the provided writing "
    "samples (and any reference URLs) and produce a concise description of the "
    "author's tone, voice, and stylistic preferences in 2-3 sentences. "
    "Use the fetch_url tool to read any URLs included in the request."
)


def analyze_style(writing_samples: list[str], reference_urls: list[str] = []) -> str:
    """
    Analyze writing samples and produce a tone and style description.

    When ``reference_urls`` are provided the agent fetches each page via the
    ``fetch_url`` tool before summarising.  With no URLs a single model call
    is made (no tools).

    :param writing_samples: Example texts provided by the user.
    :param reference_urls: Optional URLs whose content should inform the style analysis.
    :returns: A concise description of the user's writing style and tone.
    """
    parts = []
    if writing_samples:
        samples_text = "\n\n---\n\n".join(writing_samples)
        parts.append(f"Writing samples:\n\n{samples_text}")

    if reference_urls:
        urls_text = "\n".join(f"- {url}" for url in reference_urls)
        parts.append(
            f"Also fetch and consider these reference URLs when forming your analysis:\n{urls_text}"
        )
        tools = [FETCH_URL_TOOL]
    else:
        tools = []

    body = "\n\n".join(parts) if parts else "No samples or URLs provided."
    prompt = (
        f"{body}\n\n"
        f"Describe the author's tone, voice, and stylistic preferences in 2-3 sentences."
    )

    return run_agent_loop(
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        system=_SYSTEM_PROMPT,
        max_tokens=512,
    )
