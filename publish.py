#!/usr/bin/env python3
"""
AgentOS Build & Publish Script
==============================

This script builds and publishes AgentOS to PyPI.

Usage:
    python publish.py build      # Build distribution packages
    python publish.py test       # Upload to TestPyPI
    python publish.py publish    # Upload to PyPI (production)
    python publish.py clean      # Clean build artifacts
    python publish.py all        # Clean, build, and publish to PyPI

Requirements:
    pip install build twine

Environment Variables:
    TWINE_USERNAME  - PyPI username (or use __token__ for API tokens)
    TWINE_PASSWORD  - PyPI password or API token
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent.resolve()
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
EGG_INFO = ROOT_DIR / "agentos_ai.egg-info"


def run_cmd(cmd, check=True):
    """Run a shell command."""
    print(f"\n>>> {cmd}\n")
    # Use list format to handle paths with spaces properly
    result = subprocess.run(cmd, shell=True, cwd=ROOT_DIR)
    if check and result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(1)
    return result


# Quote the Python executable to handle paths with spaces
PYTHON = f'"{sys.executable}"'


def clean():
    """Remove build artifacts."""
    print("🧹 Cleaning build artifacts...")

    dirs_to_remove = [DIST_DIR, BUILD_DIR, EGG_INFO]
    for d in dirs_to_remove:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed: {d}")

    # Remove __pycache__ directories
    for pycache in ROOT_DIR.rglob("__pycache__"):
        shutil.rmtree(pycache)

    # Remove .pyc files
    for pyc in ROOT_DIR.rglob("*.pyc"):
        pyc.unlink()

    print("✅ Clean complete")


def build():
    """Build distribution packages."""
    print("📦 Building distribution packages...")

    # Ensure build tool is installed
    run_cmd(f"{PYTHON} -m pip install --upgrade build")

    # Build source distribution and wheel
    run_cmd(f"{PYTHON} -m build")

    # List built files
    if DIST_DIR.exists():
        print("\n📁 Built packages:")
        for f in DIST_DIR.iterdir():
            size = f.stat().st_size / 1024
            print(f"  {f.name} ({size:.1f} KB)")

    print("\n✅ Build complete")


def test_upload():
    """Upload to TestPyPI."""
    print("🧪 Uploading to TestPyPI...")

    # Ensure twine is installed
    run_cmd(f"{PYTHON} -m pip install --upgrade twine")

    # Upload to TestPyPI
    run_cmd(f"{PYTHON} -m twine upload --repository testpypi dist/*")

    print("\n✅ Upload to TestPyPI complete")
    print("\nTest installation with:")
    print("  pip install --index-url https://test.pypi.org/simple/ agentos-ai")


def publish():
    """Upload to PyPI (production)."""
    print("🚀 Uploading to PyPI...")

    # Confirm before publishing
    response = input("\n⚠️  This will publish to the REAL PyPI. Continue? [y/N]: ")
    if response.lower() != "y":
        print("Aborted.")
        return

    # Ensure twine is installed
    run_cmd(f"{PYTHON} -m pip install --upgrade twine")

    # Upload to PyPI
    run_cmd(f"{PYTHON} -m twine upload dist/*")

    print("\n✅ Published to PyPI!")
    print("\nInstall with:")
    print("  pip install agentos-ai")
    print("  pip install agentos-ai[full]  # Full installation")


def check():
    """Check the package before uploading."""
    print("🔍 Checking package...")

    run_cmd(f"{PYTHON} -m pip install --upgrade twine")
    run_cmd(f"{PYTHON} -m twine check dist/*")

    print("\n✅ Package check passed")


def show_help():
    """Show help message."""
    print(__doc__)
    print("\nCommands:")
    print("  build    - Build distribution packages (sdist and wheel)")
    print("  test     - Upload to TestPyPI for testing")
    print("  publish  - Upload to PyPI (production)")
    print("  clean    - Remove build artifacts")
    print("  check    - Verify package before upload")
    print("  all      - Clean, build, and publish to PyPI")
    print()


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "build":
        clean()
        build()
    elif command == "test":
        if not DIST_DIR.exists():
            clean()
            build()
        check()
        test_upload()
    elif command == "publish":
        if not DIST_DIR.exists():
            clean()
            build()
        check()
        publish()
    elif command == "clean":
        clean()
    elif command == "check":
        check()
    elif command == "all":
        clean()
        build()
        check()
        publish()
    elif command in ["help", "-h", "--help"]:
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
