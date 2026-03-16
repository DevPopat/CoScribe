"""
Intake agent — extracts writing session parameters from a natural-language conversation.

The user describes their project in free-form text. This agent analyses the
conversation, extracts structured fields (topic, audience, notes,
writing_samples, reference_urls), and decides whether enough information is
available to create a session.  It either asks a single clarifying question or
signals readiness with the extracted fields.
"""

import json
import re
import time

import anthropic

from app.agents.utils import client

_RESPONSE_SCHEMA = """
{
  "reply": "string — your message to the user",
  "ready": true | false,
  "extracted": {
    "topic": "string",
    "audience": "string",
    "notes": "string or omit if none",
    "writing_samples": ["string"] or [],
    "reference_urls": ["string"] or []
  }
}
"""

_SYSTEM_PROMPT = (
    "You are CoScribe, an AI writing copilot. Your job is to gather the information "
    "needed to start a writing session by having a natural conversation with the user.\n\n"
    "You need at minimum: topic and audience. Notes, writing samples, and reference URLs "
    "are optional extras that improve the result.\n\n"
    "Rules:\n"
    "- If both topic AND audience are clear from the conversation, set ready=true and "
    "include all extracted fields. Be generous — infer reasonable values rather than "
    "asking unnecessary questions.\n"
    "- If either topic or audience is genuinely missing, set ready=false and ask ONE "
    "concise follow-up question in reply.\n"
    "- When ready=false, omit the 'extracted' key entirely.\n"
    "- When ready=true, the 'extracted' key must be present with topic and audience.\n"
    "- writing_samples is a list of text strings the user pasted as examples of their "
    "writing style. reference_urls is a list of URLs they mentioned.\n\n"
    f"Always respond with valid JSON matching this schema:\n{_RESPONSE_SCHEMA}\n"
    "Return only valid JSON with no markdown fences or extra text."
)


def extract_session_params(messages: list[dict]) -> dict:
    """
    Analyse a conversation and extract writing session parameters.

    Passes the full message history to claude-sonnet-4-6 and returns a dict
    with ``reply``, ``ready``, and optionally ``extracted`` fields.

    :param messages: Conversation history as a list of ``{role, content}`` dicts.
    :returns: A dict with ``reply`` (str), ``ready`` (bool), and optionally
        ``extracted`` (dict with topic, audience, notes, writing_samples,
        reference_urls).
    """
    for attempt in range(5):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=messages,
            )
            break
        except anthropic.RateLimitError:
            if attempt == 4:
                raise
            time.sleep(15 * (2 ** attempt))

    raw = response.content[0].text
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw.strip())
    result = json.loads(raw)

    # Ensure extracted is absent (not None) when not ready
    if not result.get("ready") and "extracted" in result:
        del result["extracted"]

    return result
