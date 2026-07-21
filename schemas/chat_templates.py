from typing import List, Optional

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AskRequest(BaseModel):
    question: str
    history: List[ChatTurn] = Field(default_factory=list)


class Source(BaseModel):
    id: Optional[str] = None
    topic: Optional[str] = None
    guideline: Optional[str] = None
    source_org: Optional[str] = None
    source_url: Optional[str] = None
    score: Optional[float] = None


class Safety(BaseModel):
    checked: bool = False
    blocked: bool = False
    groundedness: Optional[str] = None
    medical_safety: Optional[str] = None
    violations: List[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    sources: List[Source] = Field(default_factory=list)
    safety: Safety = Field(default_factory=Safety)
