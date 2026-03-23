"""
Shared infrastructure for agentic loops across all planning agents.

Provides a shared Anthropic client, an OpenAI client, tool definitions for
web search and URL fetching, a helper for fetching and parsing HTML pages, and
``run_agent_loop()`` which drives the tool_use / end_turn cycle for any agent.
Pass ``provider="openai"`` to route the loop through OpenAI's Chat Completions
API (gpt-4o-search-preview with built-in web search + fetch_url function tool);
the default provider is ``"anthropic"``.
"""

import json
import time

import anthropic
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI

anthropic_client = anthropic.Anthropic()
openai_client = OpenAI()

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

# OpenAI function-calling equivalent of FETCH_URL_TOOL
_FETCH_URL_TOOL_OPENAI = {
    "type": "function",
    "function": {
        "name": "fetch_url",
        "description": FETCH_URL_TOOL["description"],
        "parameters": FETCH_URL_TOOL["input_schema"],
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
                response = anthropic_client.messages.create(**kwargs)
                break
            except anthropic.RateLimitError:
                if attempt == 4:
                    raise
                wait = 15 * (2 ** attempt)
                time.sleep(wait)

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

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


def _run_openai_loop(
    messages: list[dict],
    tools: list[dict],
    system: str,
) -> str:
    """
    Run a tool_use / end_turn agentic loop using the OpenAI Chat Completions API.

    Uses ``gpt-4o-search-preview`` which has built-in web search, so the
    Anthropic ``web_search_20250305`` tool is skipped; only ``fetch_url`` is
    mapped to an OpenAI function tool.

    :param messages: Initial conversation messages in Anthropic-style format
        (converted to OpenAI format internally).
    :param tools: Anthropic-format tool definitions (web_search is skipped;
        fetch_url is converted to an OpenAI function definition).
    :param system: Optional system prompt.
    :returns: The final assistant text response.
    """
    # Prepend system message and convert to OpenAI message format
    openai_messages = []
    if system:
        openai_messages.append({"role": "system", "content": system})
    openai_messages.extend(messages)

    # Build OpenAI tool list: skip built-in web_search, convert fetch_url
    openai_tools = []
    for tool in tools:
        if tool.get("name") == "fetch_url":
            openai_tools.append(_FETCH_URL_TOOL_OPENAI)
        # web_search_20250305 is built-in for gpt-4o-search-preview; skip it

    kwargs: dict = {
        "model": "gpt-4o-search-preview",
        "messages": openai_messages,
    }
    if openai_tools:
        kwargs["tools"] = openai_tools

    while True:
        response = openai_client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            return choice.message.content or ""

        # Append assistant turn with tool calls
        openai_messages.append(choice.message)
        kwargs["messages"] = openai_messages

        # Execute each tool call and append results
        for tool_call in choice.message.tool_calls:
            if tool_call.function.name == "fetch_url":
                args = json.loads(tool_call.function.arguments)
                result = _fetch_url(args.get("url", ""))
            else:
                result = ""
            openai_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )


def run_agent_loop(
    messages: list[dict],
    tools: list[dict],
    system: str = "",
    max_tokens: int = 2048,
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
    if provider == "openai":
        return _run_openai_loop(messages, tools, system)
    return _run_anthropic_loop(messages, tools, system, max_tokens)
