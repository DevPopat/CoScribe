"""
Conversational intake API endpoint.

Provides POST /chat which drives the pre-session conversation: the user
describes their writing project in natural language and the intake agent
asks clarifying questions until it has enough information, at which point
it returns the extracted session parameters.
"""

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from app.agents.intake import extract_session_params

router = APIRouter(prefix="/sessions", tags=["chat"])


class ChatMessage(BaseModel):
    """
    A single message in the intake conversation.

    :param role: Speaker — ``"user"`` or ``"assistant"``.
    :param content: Message text.
    """

    role: str
    content: str


class ChatRequest(BaseModel):
    """
    Request body for the chat intake endpoint.

    :param messages: Full conversation history, oldest first. Must contain
        at least one message.
    """

    messages: list[ChatMessage]

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v: list) -> list:
        """
        Reject empty message lists.

        :param v: The messages list to validate.
        :returns: The validated list.
        :raises ValueError: If the list is empty.
        """
        if not v:
            raise ValueError("messages must not be empty")
        return v


@router.post("/chat")
async def chat(body: ChatRequest) -> dict:
    """
    Advance the intake conversation and return the agent's response.

    Passes the full message history to the intake agent. When the agent
    has gathered enough information it sets ``ready=true`` and includes
    the extracted session parameters.

    :param body: Conversation history.
    :returns: A dict with ``reply`` (str), ``ready`` (bool), and
        optionally ``extracted`` (topic, audience, notes,
        writing_samples, reference_urls).
    """
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    return extract_session_params(messages)
