from abc import ABC, abstractmethod
from typing import Optional

from app.models.session import WritingSession


class SessionStore(ABC):
    @abstractmethod
    def create(self, session: WritingSession) -> None: ...

    @abstractmethod
    def get(self, session_id: str) -> Optional[WritingSession]: ...

    @abstractmethod
    def update(self, session: WritingSession) -> None: ...
