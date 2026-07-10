import pytest
from pydantic import ValidationError
from schemas.response_templates import Evaluation
from schemas.fast_api_templates import EvaluateRequest, EvaluateResponse, Message


# ---------------------------------------------------------------------------
# Evaluation (LLM output schema)
# ---------------------------------------------------------------------------

VALID_EVALUATION = {
    "groundedness": "PASS",
    "medical_safety": "PASS",
    "empathy_score": 2,
    "violations": [],
    "kb_ids_used": ["PH001"],
}


def test_evaluation_valid():
    ev = Evaluation(**VALID_EVALUATION)
    assert ev.groundedness == "PASS"
    assert ev.empathy_score == 2
    assert ev.kb_ids_used == ["PH001"]


def test_evaluation_invalid_empathy_score():
    with pytest.raises(ValidationError):
        Evaluation(**{**VALID_EVALUATION, "empathy_score": 5})


def test_evaluation_invalid_groundedness():
    with pytest.raises(ValidationError):
        Evaluation(**{**VALID_EVALUATION, "groundedness": "UNKNOWN"})


def test_evaluation_invalid_medical_safety():
    with pytest.raises(ValidationError):
        Evaluation(**{**VALID_EVALUATION, "medical_safety": "UNKNOWN"})


def test_evaluation_invalid_violation_label():
    with pytest.raises(ValidationError):
        Evaluation(**{**VALID_EVALUATION, "violations": ["not_a_real_violation"]})


def test_evaluation_violations_empty_on_pass():
    # violations CAN be empty when safety passes (schema allows it)
    ev = Evaluation(**{**VALID_EVALUATION, "violations": []})
    assert ev.violations == []


# ---------------------------------------------------------------------------
# EvaluateRequest
# ---------------------------------------------------------------------------

VALID_TURN = [
    {"role": "user", "content": "How much sleep do I need?"},
    {"role": "assistant", "content": "Adults need 7+ hours of sleep."},
]


def test_evaluate_request_valid():
    req = EvaluateRequest(turns=[VALID_TURN])
    assert len(req.turns) == 1
    assert req.turns[0][0].role == "user"
    assert req.turns[0][1].content == "Adults need 7+ hours of sleep."


def test_evaluate_request_invalid_role():
    bad_turn = [
        {"role": "unknown_role", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    with pytest.raises(ValidationError):
        EvaluateRequest(turns=[bad_turn])


def test_evaluate_request_missing_content():
    bad_turn = [{"role": "user"}, {"role": "assistant", "content": "hello"}]
    with pytest.raises(ValidationError):
        EvaluateRequest(turns=[bad_turn])


def test_evaluate_request_multiple_turns():
    req = EvaluateRequest(turns=[VALID_TURN, VALID_TURN])
    assert len(req.turns) == 2


# ---------------------------------------------------------------------------
# EvaluateResponse (extends Evaluation with echo fields)
# ---------------------------------------------------------------------------

def test_evaluate_response_valid():
    resp = EvaluateResponse(
        **VALID_EVALUATION,
        user_message="How much sleep do I need?",
        agent="Adults need 7+ hours of sleep.",
    )
    assert resp.user_message == "How much sleep do I need?"
    assert resp.agent == "Adults need 7+ hours of sleep."
    assert resp.groundedness == "PASS"


def test_evaluate_response_missing_echo_fields():
    with pytest.raises(ValidationError):
        EvaluateResponse(**VALID_EVALUATION)  # missing user_message and agent


def test_evaluate_response_inherits_evaluation_validation():
    with pytest.raises(ValidationError):
        EvaluateResponse(
            **{**VALID_EVALUATION, "groundedness": "WRONG"},
            user_message="q",
            agent="a",
        )