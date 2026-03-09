"""
WritingSession dataclass and SessionStatus enum.

A ``WritingSession`` holds all state for a single user writing job —
from initial topic input through planning, drafting, and completion.
The ``SessionStatus`` enum defines the allowed state transitions.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.models.outline import Outline


class SessionStatus(str, Enum):
    """
    Lifecycle states for a writing session.

    Transitions flow in order: PENDING → PLANNING → OUTLINE_READY → DRAFTING → COMPLETE.
    """

    PENDING = "pending"
    PLANNING = "planning"
    OUTLINE_READY = "outline_ready"
    DRAFTING = "drafting"
    COMPLETE = "complete"


@dataclass
class WritingSession:
    """
    All state for a single user writing job.

    :param topic: The subject the user wants to write about.
    :param audience: Intended readership (e.g. "beginners", "senior engineers").
    :param id: Unique session identifier, auto-generated as a UUID.
    :param notes: Optional freeform guidance from the user for the planning agents.
    :param writing_samples: Example texts provided by the user for style analysis.
    :param status: Current lifecycle state of the session.
    :param outline: The outline produced by the planning agents, set after planning completes.
    """

    topic: str
    audience: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notes: str = ""
    writing_samples: list[str] = field(default_factory=list)
    status: SessionStatus = SessionStatus.PENDING
    outline: Optional[Outline] = None
