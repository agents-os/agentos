#!/usr/bin/env python3
"""AgentOS Local Installer - Installs from current project directory"""

import os
import platform
import subprocess
import sys
from pathlib import Path

# Fix Windows Unicode issues
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


def run_command(cmd, cwd=None, check=True):
    """Execute shell command"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def main():
    print("=== 🤖 AgentOS Local Installer ===\n")
    
    # Get current project directory (parent of installer directory)
    project_dir = Path(__file__).parent.parent
    print(f"Installing from: {project_dir}\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("X Python 3.8+ required")
        sys.exit(1)
    print(f"+ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Install Python packages
    is_windows = platform.system().lower() == "windows"
    print("\nInstalling Python packages...")
    pip_flags = "" if is_windows else "--break-system-packages"
    
    # Upgrade pip
    run_command(f"{sys.executable} -m pip install --upgrade pip {pip_flags}", check=False)
    
    # Install critical dependencies first
    print("Installing critical dependencies...")
    run_command(f"{sys.executable} -m pip install typing-extensions setuptools wheel {pip_flags}", check=False)
    
    # Install from requirements.txt
    print("Installing dependencies from requirements.txt...")
    req_file = project_dir / "requirements.txt"
    if req_file.exists():
        run_command(f"{sys.executable} -m pip install -r {str(req_file)} {pip_flags}")
    
    # Install AgentOS in development mode
    print("Installing AgentOS...")
    run_command(f"{sys.executable} -m pip install -e {str(project_dir)} {pip_flags}")
    
    # Verify installation
    print("\nVerifying installation...")
    result = run_command(f"{sys.executable} -c 'import agentos'", check=False)
    if result.returncode != 0:
        print("! Warning: AgentOS module import failed")
        print("Trying alternative import...")
        result = run_command(f"{sys.executable} -c 'from agentos import agentos'", check=False)
        if result.returncode != 0:
            print("! Module import still failed")
        else:
            print("+ AgentOS module verified (alternative import)")
    else:
        print("+ AgentOS module verified")
    
    # Test CLI
    print("Testing CLI...")
    result = run_command(f"{sys.executable} -m agentos.agentos --help", check=False)
    if result.returncode == 0:
        print("+ CLI working")
    else:
        print("! CLI test failed, trying alternative...")
        result = run_command(f"{sys.executable} {project_dir / 'agentos.py'} --help", check=False)
        if result.returncode == 0:
            print("+ CLI working (direct script)")
        else:
            print("! CLI still not working")
    
    print("\n+ Installation complete!")
    print(f"\nAgentOS installed from: {project_dir}")
    print("\nUsage:")
    print("  python -m agentos.agentos --help")
    print(f"  python {project_dir / 'agentos.py'} --help")


if __name__ == "__main__":
    main()