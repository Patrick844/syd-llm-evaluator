import yaml
import json

def get_config(config_name, path="config/config.yaml", ):
    """
    Load a named config block from YAML.

    Args:
        config_name: Top-level key inside the YAML file.
        path: Path to the YAML config file.
    """
    try:
        with open(path, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config file not found: {path}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {path}") from e

    try:
        return config[config_name]
    except Exception as e:
        raise KeyError(f"Config key '{config_name}' not found in {path}") from e


def get_dataset(path):
    """
    Load newline-delimited JSON (JSONL) into a Python list.
    Each line is expected to be a standalone JSON object.
    """
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Dataset file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON line in dataset file: {path}") from e

    return rows


def get_kb(path):
    """
    Load a standard JSON file containing knowledge base entries.
    """
    rows = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            rows = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Knowledge base file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in knowledge base file: {path}") from e

    return rows