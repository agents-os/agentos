"""
Path Resolution Utility for AgentOS
Handles finding files and directories from any working directory
"""

from pathlib import Path
from typing import Optional


def resolve_manifest_path(manifest_name: str) -> Optional[Path]:
    """
    Resolve manifest file path from multiple locations.

    Search order:
    1. Absolute path (if provided)
    2. Current working directory
    3. Home directory
    4. Project root directory
    5. Examples directory

    Args:
        manifest_name: Name or path of the manifest file

    Returns:
        Resolved Path object or None if not found
    """
    search_paths = [
        Path(manifest_name),  # Absolute or relative to cwd
        Path.cwd() / manifest_name,  # Current working directory
        Path.home() / manifest_name,  # Home directory
        get_project_root() / manifest_name,  # Project root
        get_project_root() / "examples" / manifest_name,  # Examples directory
    ]

    for path in search_paths:
        if path.exists() and path.is_file():
            return path.resolve()

    return None


def resolve_yaml_path(yaml_name: str) -> Optional[Path]:
    """Alias for resolve_manifest_path for YAML files"""
    return resolve_manifest_path(yaml_name)


def get_package_dir() -> Path:
    """
    Get the agentos package directory.

    Returns the agentos package directory (where __init__.py is).
    This works both in development and when installed via pip.
    """
    # Get the directory of this file (agentos/core/)
    current_file = Path(__file__).resolve()
    # Go up to agentos/
    package_dir = current_file.parent.parent
    return package_dir


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns the directory containing the agentos package.
    For development use only - not reliable when installed via pip.
    """
    return get_package_dir().parent


def get_examples_dir() -> Path:
    """Get the examples directory"""
    # First try inside package (for pip installs)
    pkg_examples = get_package_dir() / "examples"
    if pkg_examples.exists():
        return pkg_examples
    # Fallback to project root (for development)
    return get_project_root() / "examples"


def get_templates_dir() -> Path:
    """Get the templates directory"""
    # Templates are now inside the agentos package
    return get_package_dir() / "templates"


def get_static_dir() -> Path:
    """Get the static files directory"""
    # Static files are now inside the agentos package
    return get_package_dir() / "static"


def find_all_manifests() -> list:
    """
    Find all manifest files in searchable locations.

    Returns:
        List of Path objects for all found manifest files
    """
    manifests = []
    search_dirs = [
        Path.cwd(),
        Path.home(),
        get_project_root(),
        get_examples_dir(),
    ]

    for search_dir in search_dirs:
        if search_dir.exists():
            for yaml_file in search_dir.glob("*.yaml"):
                if yaml_file not in manifests:
                    manifests.append(yaml_file)

    return manifests


def ensure_directory_exists(directory: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to directory

    Returns:
        The directory path
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_working_directory() -> Path:
    """Get the current working directory"""
    return Path.cwd()


def is_absolute_path(path_str: str) -> bool:
    """Check if a path string is absolute"""
    return Path(path_str).is_absolute()


def make_path_relative_to_cwd(path: Path) -> Path:
    """
    Convert an absolute path to be relative to current working directory if possible.

    Args:
        path: Path object

    Returns:
        Relative path if possible, otherwise absolute path
    """
    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


def make_path_absolute(path_str: str) -> Path:
    """
    Convert a path string to an absolute path.

    Args:
        path_str: Path string (absolute or relative)

    Returns:
        Absolute Path object
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


if __name__ == "__main__":
    print("AgentOS Path Resolver")
    print(f"Project Root: {get_project_root()}")
    print(f"Current Working Directory: {get_working_directory()}")
    print(f"Examples Directory: {get_examples_dir()}")
    print(f"Templates Directory: {get_templates_dir()}")
    print(f"Static Directory: {get_static_dir()}")
    print(f"\nFound Manifests:")
    for manifest in find_all_manifests():
        print(f"  - {manifest}")
