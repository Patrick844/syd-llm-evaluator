from config.llm_config import LLM_OPENAI
from utils import get_config
from schemas.response_templates import Evaluation


def run_llm(kb, user_message):
    """
    Run evaluator LLM with configured prompt/schema.

    Args:
        kb: Pre-loaded knowledge base entries (injected by caller).
        user_message: Input payload passed to model.
    """
    try:
        # Read evaluator settings from config/config.yaml.
        config = get_config("llm_evaluator")
        config["system_prompt"] = str(config["system_prompt"]).format(kb=str(kb))
    except Exception as e:
        raise RuntimeError(f"Failed preparing LLM evaluation config: {e}") from e

    try:
        # Build model client and request structured output.
        llm = LLM_OPENAI(config)
        response = llm.invoke(user_message, Evaluation)
        return response
    except Exception as e:
        raise RuntimeError(f"LLM invocation failed: {e}") from e
