import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.models.outline import Outline


class SessionStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    OUTLINE_READY = "outline_ready"
    DRAFTING = "drafting"
    COMPLETE = "complete"


@dataclass
class WritingSession:
    topic: str
    audience: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notes: str = ""
    writing_samples: list[str] = field(default_factory=list)
    status: SessionStatus = SessionStatus.PENDING
    outline: Optional[Outline] = None
