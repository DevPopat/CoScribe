from typing import Optional
from pydantic import BaseModel


class Section(BaseModel):
    title: str
    key_points: list[str]
    draft: Optional[str] = None
    approved: bool = False


class Outline(BaseModel):
    title: str
    brief: str
    tone_guidance: str
    sections: list[Section]
