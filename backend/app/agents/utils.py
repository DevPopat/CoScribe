"""
Shared infrastructure for agentic loops across all planning agents.

Provides a shared Anthropic client, tool definitions for web search and URL
fetching, a helper for fetching and parsing HTML pages, and
``run_agent_loop()`` which drives the tool_use / end_turn cycle for any agent.
"""

import time

import anthropic
import httpx
from bs4 import BeautifulSoup

client = anthropic.Anthropic()

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


def run_agent_loop(
    messages: list[dict],
    tools: list[dict],
    system: str = "",
    max_tokens: int = 2048,
) -> str:
    """
    Run a tool_use / end_turn agentic loop and return the final text response.

    Iterates until the model returns ``stop_reason="end_turn"``. On each
    ``tool_use`` turn, ``fetch_url`` calls are executed locally; all other
    tool calls (including server-side ``web_search``) fall through to an
    empty result — the catch-all ``else`` branch handles any unrecognised tool.

    :param messages: Initial conversation messages in Anthropic format.
    :param tools: List of tool definitions to pass to the model.
    :param system: Optional system prompt.
    :param max_tokens: Maximum tokens for each model call.
    :returns: The final assistant text response.
    """
    messages = list(messages)

    while True:
        kwargs = dict(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            tools=tools,
            messages=messages,
        )
        if system:
            kwargs["system"] = system

        for attempt in range(5):
            try:
                response = client.messages.create(**kwargs)
                break
            except anthropic.RateLimitError:
                if attempt == 4:
                    raise
                wait = 15 * (2 ** attempt)
                time.sleep(wait)

        # Continue the loop only when the model explicitly requests tool use.
        # For all other stop reasons (end_turn, max_tokens, etc.), return text.
        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Handle client-side tool_use blocks
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "fetch_url":
                    result = _fetch_url(block.input.get("url", ""))
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
