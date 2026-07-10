import json
import pytest
from unittest.mock import mock_open, patch
from utils import get_config, get_dataset, get_kb


# ---------------------------------------------------------------------------
# get_config
# ---------------------------------------------------------------------------

SAMPLE_YAML = "llm_evaluator:\n  model_name: gpt-4.1\n  response_type: structured_output\n"


def test_get_config_returns_block():
    with patch("builtins.open", mock_open(read_data=SAMPLE_YAML)):
        config = get_config("llm_evaluator")
    assert config["model_name"] == "gpt-4.1"
    assert config["response_type"] == "structured_output"


def test_get_config_missing_file():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            get_config("llm_evaluator")


def test_get_config_invalid_yaml():
    with patch("builtins.open", mock_open(read_data=":\ninvalid: [yaml")):
        with pytest.raises(ValueError, match="Invalid YAML"):
            get_config("llm_evaluator")


def test_get_config_missing_key():
    with patch("builtins.open", mock_open(read_data=SAMPLE_YAML)):
        with pytest.raises(KeyError, match="nonexistent"):
            get_config("nonexistent")


# ---------------------------------------------------------------------------
# get_kb
# ---------------------------------------------------------------------------

SAMPLE_KB = [{"id": "PH001", "topic": "Sleep", "guideline": "Sleep 7+ hours."}]


def test_get_kb_returns_list():
    with patch("builtins.open", mock_open(read_data=json.dumps(SAMPLE_KB))):
        kb = get_kb("any/path.json")
    assert len(kb) == 1
    assert kb[0]["id"] == "PH001"


def test_get_kb_missing_file():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match="Knowledge base file not found"):
            get_kb("missing.json")


def test_get_kb_invalid_json():
    with patch("builtins.open", mock_open(read_data="{not valid json")):
        with pytest.raises(ValueError, match="Invalid JSON"):
            get_kb("bad.json")


# ---------------------------------------------------------------------------
# get_dataset
# ---------------------------------------------------------------------------

SAMPLE_JSONL = '{"user": "hi", "agent": "hello"}\n{"user": "bye", "agent": "goodbye"}\n'


def test_get_dataset_returns_rows():
    with patch("builtins.open", mock_open(read_data=SAMPLE_JSONL)):
        rows = get_dataset("any/path.jsonl")
    assert len(rows) == 2
    assert rows[0]["user"] == "hi"


def test_get_dataset_missing_file():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError, match="Dataset file not found"):
            get_dataset("missing.jsonl")


def test_get_dataset_invalid_json_line():
    with patch("builtins.open", mock_open(read_data="not json\n")):
        with pytest.raises(ValueError, match="Invalid JSON line"):
            get_dataset("bad.jsonl")
