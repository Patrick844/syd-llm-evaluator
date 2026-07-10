from typing import List, Literal
from pydantic import BaseModel
from schemas.response_templates import Evaluation


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class EvaluateRequest(BaseModel):
    # Each turn is a pair of [user message, assistant message].
    turns: List[List[Message]]


class EvaluateResponse(Evaluation):
    # Echo of the original user message for dashboard display.
    user_message: str
    # Echo of the agent response being evaluated.
    agent: str
