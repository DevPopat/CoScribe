"""
Intake agent — extracts writing session parameters from a natural-language conversation.

The user describes their project in free-form text. This agent analyses the
conversation, extracts structured fields (topic, audience, notes,
writing_samples, reference_urls), and decides whether enough information is
available to create a session.  It either asks a single clarifying question or
signals readiness with the extracted fields.
"""

import json
import logging
import re
import time

import anthropic

from app.agents.utils import anthropic_client as client, safe_json_loads

logger = logging.getLogger(__name__)

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
    "Follow this two-step process:\n\n"
    "Step 1 — Topic and audience.\n"
    "If either is missing, ask ONE concise question to get it. Do not ask for anything "
    "else yet.\n\n"
    "Step 2 — Writing samples.\n"
    "Once topic and audience are both clear, ask the user for writing samples BEFORE "
    "marking ready. Writing samples can be URLs to previous articles/posts OR pasted "
    "text — both are useful for matching tone and style. Ask: something like "
    "'Do you have any writing samples or previous articles I can use to match your style? "
    "Share URLs or paste text — or just say skip.' "
    "Only mark ready=true after the user responds to this question (even if they skip).\n\n"
    "Rules:\n"
    "- ready=false: omit the 'extracted' key entirely.\n"
    "- ready=true: 'extracted' must be present with topic and audience.\n"
    "- writing_samples: list of raw text strings the user pasted.\n"
    "- reference_urls: list of URLs the user shared as writing samples or references.\n"
    "- notes: any extra guidance the user mentioned (tone, angle, word count, etc.).\n"
    "- Ask at most ONE question per turn. Never ask two things at once.\n\n"
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
    logger.info("[intake] extracting params — %d messages in history", len(messages))

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
            wait = 15 * (2 ** attempt)
            logger.warning("[intake] rate limited, attempt %d/5, retrying in %ds", attempt + 1, wait)
            if attempt == 4:
                raise
            time.sleep(wait)

    # Log every content block the model returned
    logger.info("[intake] stop_reason=%s, content_blocks=%d", response.stop_reason, len(response.content))
    for i, block in enumerate(response.content):
        block_type = getattr(block, "type", "unknown")
        block_text = getattr(block, "text", None)
        logger.info("[intake] block[%d] type=%s text=%s", i, block_type, repr(block_text[:500]) if block_text else "None")

    # Extract text from the first text block (skip non-text blocks)
    raw = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            raw = block.text
            break

    if not raw:
        logger.error("[intake] no text block found in response — returning fallback")
        return {"reply": "Sorry, something went wrong. Could you try again?", "ready": False}

    logger.info("[intake] raw response (%d chars):\n%s", len(raw), raw)

    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw.strip())

    try:
        result = safe_json_loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("[intake] json.loads failed: %s — attempting regex extraction", exc)
        logger.warning("[intake] problematic raw text:\n%s", raw)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            logger.info("[intake] regex extracted JSON (%d chars)", len(match.group()))
            result = safe_json_loads(match.group())
        else:
            logger.error("[intake] no JSON found — returning raw text as reply")
            return {"reply": raw or "Sorry, something went wrong. Could you try again?", "ready": False}

    logger.info("[intake] parsed result — ready=%s, has_extracted=%s", result.get("ready"), "extracted" in result)

    # Ensure extracted is absent (not None) when not ready
    if not result.get("ready") and "extracted" in result:
        del result["extracted"]

    return result
