"""
Shared infrastructure for agentic loops across all planning agents.

Provides a shared Anthropic client, an OpenAI client, tool definitions for
web search and URL fetching, a helper for fetching and parsing HTML pages, and
``run_agent_loop()`` which drives the tool_use / end_turn cycle for any agent.
Pass ``provider="openai"`` to route the loop through OpenAI's Chat Completions
API (gpt-4o-search-preview with built-in web search + fetch_url function tool);
the default provider is ``"anthropic"``.
"""

import logging
import time

import anthropic
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI

logger = logging.getLogger(__name__)

anthropic_client = anthropic.Anthropic()
_openai_client: "OpenAI | None" = None


def _get_openai_client() -> OpenAI:
    """Return the shared OpenAI client, creating it on first use."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI()
    return _openai_client

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
}

FETCH_URL_TOOL = {
    "type": "custom",
    "name": "fetch_url",
    "description": (
        "Fetch the text content of a URL. Use this to read reference pages "
        "or articles provided by the user."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch."}
        },
        "required": ["url"],
    },
}


def _fetch_url(url: str) -> str:
    """
    Fetch a URL and return its visible text content.

    Uses httpx for the HTTP request and BeautifulSoup to strip HTML tags,
    returning only the readable text of the page.

    :param url: The URL to retrieve.
    :returns: Visible text extracted from the page, or an error message if
        the request fails.
    """
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except Exception as exc:
        return f"Error fetching {url}: {exc}"


def _run_anthropic_loop(
    messages: list[dict],
    tools: list[dict],
    system: str,
    max_tokens: int,
) -> str:
    """
    Run a tool_use / end_turn agentic loop using the Anthropic API.

    :param messages: Initial conversation messages in Anthropic format.
    :param tools: Anthropic-format tool definitions.
    :param system: Optional system prompt.
    :param max_tokens: Maximum tokens per model call.
    :returns: The final assistant text response.
    """
    messages = list(messages)
    turn = 0

    while True:
        turn += 1
        kwargs = dict(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            tools=tools,
            messages=messages,
        )
        if system:
            kwargs["system"] = system

        logger.info("[anthropic] turn %d — calling model (tools=%s)", turn, [t.get("name", t.get("type")) for t in tools])

        for attempt in range(5):
            try:
                response = anthropic_client.messages.create(**kwargs)
                break
            except anthropic.RateLimitError:
                wait = 15 * (2 ** attempt)
                logger.warning("[anthropic] turn %d — rate limited, attempt %d/5, retrying in %ds", turn, attempt + 1, wait)
                if attempt == 4:
                    raise
                time.sleep(wait)

        logger.info("[anthropic] turn %d — stop_reason=%s, content_blocks=%d", turn, response.stop_reason, len(response.content))

        # If the response was truncated, feed it back and ask for a shorter version.
        if response.stop_reason == "max_tokens":
            logger.warning("[anthropic] turn %d — hit max_tokens, asking model to retry concisely", turn)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": (
                    "Your response was cut off because it exceeded the token limit. "
                    "Please provide a much shorter and more concise response in the "
                    "same JSON format. Summarize key points only — do not include "
                    "extensive detail, code blocks, or long explanations."
                ),
            })
            continue

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    logger.info("[anthropic] turn %d — final text (%d chars): %.500s", turn, len(block.text), block.text)
                    return block.text
            logger.warning("[anthropic] turn %d — no text block in final response", turn)
            return ""

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                logger.info("[anthropic] turn %d — tool_use: %s(input=%s)", turn, block.name, str(block.input)[:200])
                if block.name == "fetch_url":
                    result = _fetch_url(block.input.get("url", ""))
                    logger.info("[anthropic] turn %d — fetch_url result (%d chars)", turn, len(result))
                else:
                    result = ""
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results or "Continue."})


def _run_openai_loop(
    messages: list[dict],
    tools: list[dict],
    system: str,
) -> str:
    """
    Call the OpenAI Chat Completions API (gpt-4o-search-preview).

    This model does not support function-calling tools, so ``tools`` is
    accepted for interface compatibility but ignored.  Callers that need URL
    fetching should pre-fetch content and inline it in the prompt.

    :param messages: Conversation messages (same format as Anthropic).
    :param tools: Ignored — kept for interface compatibility with the
        Anthropic loop.
    :param system: Optional system prompt.
    :returns: The model's text response.
    """
    openai_messages: list[dict] = []
    if system:
        openai_messages.append({"role": "system", "content": system})
    openai_messages.extend(messages)

    logger.info("[openai] calling gpt-4o-search-preview (messages=%d)", len(openai_messages))

    client = _get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=openai_messages,
    )
    text = response.choices[0].message.content or ""
    logger.info("[openai] response finish_reason=%s, text (%d chars): %.500s", response.choices[0].finish_reason, len(text), text)
    return text


def run_agent_loop(
    messages: list[dict],
    tools: list[dict],
    system: str = "",
    max_tokens: int = 16384,
    provider: str = "anthropic",
) -> str:
    """
    Run a tool_use / end_turn agentic loop and return the final text response.

    Routes to either the Anthropic or OpenAI backend depending on ``provider``.
    Both backends support the same ``fetch_url`` custom tool; the Anthropic
    backend additionally supports the ``web_search_20250305`` built-in tool,
    while the OpenAI backend uses ``gpt-4o-search-preview`` which has web
    search built-in.

    :param messages: Initial conversation messages in Anthropic format.
    :param tools: List of tool definitions to pass to the model.
    :param system: Optional system prompt.
    :param max_tokens: Maximum tokens for each model call (Anthropic only).
    :param provider: ``"anthropic"`` (default) or ``"openai"``.
    :returns: The final assistant text response.
    """
    logger.info("[agent_loop] provider=%s, tools=%s", provider, [t.get("name", t.get("type")) for t in tools])
    if provider == "openai":
        return _run_openai_loop(messages, tools, system)
    return _run_anthropic_loop(messages, tools, system, max_tokens)
