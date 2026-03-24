"""
Style analyzer agent — learns tone and writing preferences from user samples.

Runs on OpenAI (gpt-4o-search-preview) so that it executes concurrently with
the Anthropic-backed research agent without sharing the same rate-limit pool.
Reference URLs are pre-fetched and their text is inlined in the prompt, so no
tool-calling is needed on the OpenAI side.
"""

import logging

from app.agents.utils import _fetch_url, run_agent_loop

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a writing style analyst. Your job is to study the provided writing "
    "samples (and any reference page content) and produce a concise description "
    "of the author's tone, voice, and stylistic preferences in 2-3 sentences."
)


def analyze_style(writing_samples: list[str], reference_urls: list[str] = []) -> str:
    """
    Analyze writing samples and produce a tone and style description.

    Reference URLs are fetched up-front and their visible text is included in
    the prompt alongside the raw writing samples.

    :param writing_samples: Example texts provided by the user.
    :param reference_urls: Optional URLs whose content should inform the style analysis.
    :returns: A concise description of the user's writing style and tone.
    """
    logger.info("[style] starting analyze_style — samples=%d, urls=%d", len(writing_samples), len(reference_urls))

    parts = []
    if writing_samples:
        samples_text = "\n\n---\n\n".join(writing_samples)
        parts.append(f"Writing samples:\n\n{samples_text}")
        logger.info("[style] included %d writing sample(s) (%d chars total)", len(writing_samples), len(samples_text))

    if reference_urls:
        for url in reference_urls:
            logger.info("[style] fetching reference URL: %s", url)
            content = _fetch_url(url)
            logger.info("[style] fetched %s — %d chars", url, len(content))
            parts.append(f"Reference page ({url}):\n\n{content}")

    body = "\n\n".join(parts) if parts else "No samples or URLs provided."
    prompt = (
        f"{body}\n\n"
        "Describe the author's tone, voice, and stylistic preferences in 2-3 sentences."
    )
    logger.info("[style] prompt length: %d chars", len(prompt))

    result = run_agent_loop(
        messages=[{"role": "user", "content": prompt}],
        tools=[],
        system=_SYSTEM_PROMPT,
        provider="openai",
    )
    logger.info("[style] result (%d chars): %.500s", len(result), result)
    return result
