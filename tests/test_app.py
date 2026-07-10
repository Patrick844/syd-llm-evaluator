import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from schemas.response_templates import Evaluation

SAMPLE_KB = [{"id": "PH001", "topic": "Sleep", "guideline": "Sleep 7+ hours."}]

SAMPLE_EVALUATION = Evaluation(
    groundedness="PASS",
    medical_safety="PASS",
    empathy_score=2,
    violations=[],
    kb_ids_used=["PH001"],
)

VALID_PAYLOAD = {
    "turns": [
        [
            {"role": "user", "content": "How much sleep do I need?"},
            {"role": "assistant", "content": "Adults need 7+ hours of sleep."},
        ]
    ]
}


@pytest.fixture()
def client_with_kb():
    """TestClient with a loaded KB and mocked LLM."""
    with patch("app.KNOWLEDGE_BASE", SAMPLE_KB), \
         patch("app.run_llm", return_value=SAMPLE_EVALUATION):
        from app import app
        yield TestClient(app)


@pytest.fixture()
def client_no_kb():
    """TestClient simulating a failed KB load."""
    with patch("app.KNOWLEDGE_BASE", []):
        from app import app
        yield TestClient(app)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_ok():
    with patch("app.KNOWLEDGE_BASE", SAMPLE_KB):
        from app import app
        client = TestClient(app)
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["kb_items"] == len(SAMPLE_KB)


def test_health_empty_kb():
    with patch("app.KNOWLEDGE_BASE", []):
        from app import app
        client = TestClient(app)
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["kb_items"] == 0


# ---------------------------------------------------------------------------
# POST /evaluate — success path
# ---------------------------------------------------------------------------

def test_evaluate_success(client_with_kb):
    resp = client_with_kb.post("/evaluate", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["groundedness"] == "PASS"
    assert result["medical_safety"] == "PASS"
    assert result["empathy_score"] == 2
    assert result["user_message"] == "How much sleep do I need?"
    assert result["agent"] == "Adults need 7+ hours of sleep."


def test_evaluate_multiple_turns(client_with_kb):
    payload = {"turns": [VALID_PAYLOAD["turns"][0], VALID_PAYLOAD["turns"][0]]}
    resp = client_with_kb.post("/evaluate", json=payload)
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 2


# ---------------------------------------------------------------------------
# POST /evaluate — error paths
# ---------------------------------------------------------------------------

def test_evaluate_kb_not_loaded(client_no_kb):
    resp = client_no_kb.post("/evaluate", json=VALID_PAYLOAD)
    assert resp.status_code == 500
    assert "Knowledge base is not loaded" in resp.json()["detail"]


def test_evaluate_llm_failure():
    with patch("app.KNOWLEDGE_BASE", SAMPLE_KB), \
         patch("app.run_llm", side_effect=RuntimeError("LLM timeout")):
        from app import app
        client = TestClient(app)
        resp = client.post("/evaluate", json=VALID_PAYLOAD)
    assert resp.status_code == 502
    assert "LLM evaluation failed" in resp.json()["detail"]


def test_evaluate_invalid_role():
    bad_payload = {
        "turns": [
            [
                {"role": "invalid_role", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ]
        ]
    }
    with patch("app.KNOWLEDGE_BASE", SAMPLE_KB):
        from app import app
        client = TestClient(app)
        resp = client.post("/evaluate", json=bad_payload)
    assert resp.status_code == 422


def test_evaluate_missing_content_field():
    bad_payload = {
        "turns": [
            [
                {"role": "user"},
                {"role": "assistant", "content": "hello"},
            ]
        ]
    }
    with patch("app.KNOWLEDGE_BASE", SAMPLE_KB):
        from app import app
        client = TestClient(app)
        resp = client.post("/evaluate", json=bad_payload)
    assert resp.status_code == 422
