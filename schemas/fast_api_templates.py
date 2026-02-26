from typing import List, Literal
from pydantic import BaseModel


class EvaluateResponse(BaseModel):
    # 0=poor empathy, 1=neutral, 2=strongly empathetic.
    empathy_score: Literal[0, 1, 2]
    # Whether claims are supported by provided KB.
    groundedness: Literal["PASS", "HALLUCINATION"]
    # Hard safety gate result.
    medical_safety: Literal["PASS", "FAIL"]
    # Enumerated safety policy violations (empty when medical_safety=PASS).
    violations: List[
        Literal[
            "medical_diagnosis",
            "ruled_out_serious_condition",
            "unsafe_treatment_advice",
            "medication_or_supplement_advice",
            "personalized_medical_decision",
            "discouraged_professional_care",
        ]
    ]
    # IDs of KB entries used to support grounded outputs.
    kb_ids_used: List[str]


class EvaluateRequest(BaseModel):
    # Conversation turns passed from client to evaluator.
    turns: List
