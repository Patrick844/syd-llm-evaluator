import pytest
from unittest.mock import MagicMock, patch
from schemas.response_templates import Evaluation

SAMPLE_KB = [{"id": "PH001", "topic": "Sleep", "guideline": "Sleep 7+ hours."}]

SAMPLE_EVALUATION = Evaluation(
    groundedness="PASS",
    medical_safety="PASS",
    empathy_score=2,
    violations=[],
    kb_ids_used=["PH001"],
)

SAMPLE_CONFIG = {
    "model_name": "gpt-4.1",
    "response_type": "structured_output",
    "system_prompt": "You are an evaluator. KB: {kb}",
}


def test_run_llm_success():
    with patch("ai_services.ai_service.get_config", return_value=dict(SAMPLE_CONFIG)) as mock_cfg, \
         patch("ai_services.ai_service.LLM_OPENAI") as mock_llm_cls:

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = SAMPLE_EVALUATION
        mock_llm_cls.return_value = mock_llm

        from ai_services.ai_service import run_llm
        result = run_llm(SAMPLE_KB, "test message")

    assert result == SAMPLE_EVALUATION
    mock_cfg.assert_called_once_with("llm_evaluator")
    mock_llm.invoke.assert_called_once()


def test_run_llm_uses_passed_kb_not_disk():
    """Ensure run_llm uses the kb argument — get_kb must not be imported in ai_service."""
    import ai_services.ai_service as ai_svc
    assert not hasattr(ai_svc, "get_kb"), (
        "get_kb should not be imported in ai_service.py; "
        "the pre-loaded kb parameter must be used instead."
    )


def test_run_llm_injects_kb_into_prompt():
    captured_config = {}

    def fake_llm_init(config):
        captured_config.update(config)
        m = MagicMock()
        m.invoke.return_value = SAMPLE_EVALUATION
        return m

    with patch("ai_services.ai_service.get_config", return_value=dict(SAMPLE_CONFIG)), \
         patch("ai_services.ai_service.LLM_OPENAI", side_effect=fake_llm_init):

        from ai_services.ai_service import run_llm
        run_llm(SAMPLE_KB, "test message")

    assert str(SAMPLE_KB) in captured_config["system_prompt"]


def test_run_llm_config_error_raises_runtime():
    with patch("ai_services.ai_service.get_config", side_effect=KeyError("llm_evaluator")):
        from ai_services.ai_service import run_llm
        with pytest.raises(RuntimeError, match="Failed preparing LLM evaluation config"):
            run_llm(SAMPLE_KB, "test message")


def test_run_llm_llm_invocation_error_raises_runtime():
    with patch("ai_services.ai_service.get_config", return_value=dict(SAMPLE_CONFIG)), \
         patch("ai_services.ai_service.LLM_OPENAI") as mock_llm_cls:

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("OpenAI timeout")
        mock_llm_cls.return_value = mock_llm

        from ai_services.ai_service import run_llm
        with pytest.raises(RuntimeError, match="LLM invocation failed"):
            run_llm(SAMPLE_KB, "test message")
