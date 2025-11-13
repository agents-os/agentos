import json
import sys
from pathlib import Path

import yaml

from agentos.core import path_resolver


def yaml_to_json(yaml_path: str):
    """
    Reads a YAML file and returns its JSON representation as a Python dict.
    Supports both absolute and relative paths.
    Uses path_resolver to find files from multiple locations.
    """
    # Try to resolve the path using path resolver
    resolved_path = path_resolver.resolve_yaml_path(yaml_path)
    
    if resolved_path is None:
        raise FileNotFoundError(
            f"YAML file not found: {yaml_path}\n"
            f"Searched in:\n"
            f"  - {Path.cwd() / yaml_path}\n"
            f"  - {Path.home() / yaml_path}\n"
            f"  - {path_resolver.get_project_root() / yaml_path}\n"
            f"  - {path_resolver.get_examples_dir() / yaml_path}"
        )

    with open(resolved_path, "r", encoding="utf-8") as file:
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
