import json
import sys
from pathlib import Path

import yaml


def yaml_to_json(yaml_path: str):
    """
    Reads a YAML file and returns its JSON representation as a Python dict.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return data


if __name__ == "__main__":
    # Default file name
    yaml_file = "default.yaml"

    # Allow command-line argument override
    if len(sys.argv) > 1:
        yaml_file = sys.argv[1]

    try:
        result = yaml_to_json(yaml_file)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
