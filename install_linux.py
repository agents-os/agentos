#!/usr/bin/env python3
"""
AgentOS Installer - Linux
=========================

This script installs AgentOS on Linux systems.

Usage:
    python3 install_linux.py [--no-venv] [--skip-api-keys]

Options:
    --no-venv       Install globally instead of virtual environment
    --skip-api-keys Skip API key configuration prompt

Repository: https://github.com/agents-os/agentos
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_step(msg):
    print(f"{Colors.BLUE}==>{Colors.END} {msg}")


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")


def run_cmd(cmd, cwd=None, check=True, capture=True):
    """Execute a shell command."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=capture, text=True
        )
        if check and result.returncode != 0:
            if capture:
                print_error(f"Command failed: {cmd}")
                if result.stderr:
                    print(result.stderr)
            return None
        return result
    except Exception as e:
        print_error(f"Error running command: {e}")
        return None


def check_python():
    """Check Python version."""
    if sys.version_info < (3, 8):
        print_error(
            f"Python 3.8+ required. You have {sys.version_info.major}.{sys.version_info.minor}"
        )
        sys.exit(1)
    print_success(
        f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )


def check_system_deps():
    """Check and install system dependencies."""
    print_step("Checking system dependencies...")

    # Check for pip
    result = run_cmd(f"{sys.executable} -m pip --version", check=False)
    if result is None or result.returncode != 0:
        print_warning("pip not found, attempting to install...")
        run_cmd("sudo apt update && sudo apt install -y python3-pip", check=False)

    # Optional: check for git (useful but not required for local install)
    result = run_cmd("which git", check=False)
    if result and result.returncode == 0:
        print_success("Git available")
    else:
        print_warning("Git not found (optional, for updates)")


def create_virtual_env(install_dir):
    """Create a virtual environment."""
    venv_path = install_dir / "venv"

    if venv_path.exists():
        print_warning(f"Virtual environment exists at {venv_path}")
        response = input("Recreate? [y/N]: ").strip().lower()
        if response == "y":
            shutil.rmtree(venv_path)
        else:
            return venv_path

    print_step("Creating virtual environment...")
    result = run_cmd(f"{sys.executable} -m venv {venv_path}")
    if result is None:
        print_error("Failed to create virtual environment")
        sys.exit(1)

    print_success(f"Virtual environment created at {venv_path}")
    return venv_path


def get_pip_cmd(venv_path=None):
    """Get the pip command for the environment."""
    if venv_path:
        return str(venv_path / "bin" / "pip")
    return f"{sys.executable} -m pip"


def get_python_cmd(venv_path=None):
    """Get the python command for the environment."""
    if venv_path:
        return str(venv_path / "bin" / "python")
    return sys.executable


def install_packages(source_dir, venv_path=None):
    """Install AgentOS and dependencies."""
    pip_cmd = get_pip_cmd(venv_path)

    print_step("Upgrading pip...")
    run_cmd(f"{pip_cmd} install --upgrade pip", check=False)

    print_step("Installing dependencies...")
    req_file = source_dir / "requirements.txt"
    if req_file.exists():
        result = run_cmd(f"{pip_cmd} install -r {req_file}")
        if result is None:
            print_error("Failed to install dependencies")
            sys.exit(1)

    print_step("Installing AgentOS...")
    result = run_cmd(f"{pip_cmd} install -e {source_dir}")
    if result is None:
        print_error("Failed to install AgentOS")
        sys.exit(1)

    print_success("All packages installed")


def configure_api_keys(install_dir):
    """Configure API keys interactively."""
    print(f"\n{Colors.BOLD}=== API Configuration ==={Colors.END}\n")
    print("Enter your API keys (press Enter to skip):\n")

    api_keys = {
        "GITHUB_TOKEN": ("GitHub Token (for GitHub Models)", ""),
        "OPENAI_API_KEY": ("OpenAI API Key", ""),
        "ANTHROPIC_API_KEY": ("Anthropic/Claude API Key", ""),
        "GEMINI_API_KEY": ("Google Gemini API Key", ""),
        "COHERE_API_KEY": ("Cohere API Key", ""),
    }

    configured_keys = {}
    for key, (description, _) in api_keys.items():
        value = input(f"{description}: ").strip()
        if value:
            configured_keys[key] = value

    # Create .env file
    env_file = install_dir / ".env"
    env_content = "# AgentOS API Keys\n"
    env_content += "# Add your API keys here\n\n"

    for key in api_keys:
        if key in configured_keys:
            env_content += f"{key}={configured_keys[key]}\n"
        else:
            env_content += f"# {key}=your_key_here\n"

    env_file.write_text(env_content)

    if configured_keys:
        print_success(f"API keys saved to {env_file}")
    else:
        print_warning(f"No API keys configured. Edit {env_file} later.")


def create_cli_wrapper(install_dir, venv_path=None):
    """Create CLI wrapper script."""
    python_cmd = get_python_cmd(venv_path)

    # Create wrapper script
    wrapper_path = install_dir / "agentos"
    wrapper_content = f"""#!/bin/bash
# AgentOS CLI Wrapper
cd "{install_dir}"
{python_cmd} -m agentos.agentos "$@"
"""
    wrapper_path.write_text(wrapper_content)
    os.chmod(wrapper_path, 0o755)

    # Try to create symlink in user's local bin
    local_bin = Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)

    symlink_path = local_bin / "agentos"
    if symlink_path.exists():
        symlink_path.unlink()

    try:
        symlink_path.symlink_to(wrapper_path)
        print_success(f"CLI available at: {symlink_path}")

        # Check if ~/.local/bin is in PATH
        if str(local_bin) not in os.environ.get("PATH", ""):
            print_warning(f"Add {local_bin} to your PATH:")
            print(f"  echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc")
            print(f"  source ~/.bashrc")
    except Exception as e:
        print_warning(f"Could not create symlink: {e}")
        print(f"Run AgentOS with: {wrapper_path}")


def create_desktop_entry(install_dir, venv_path=None):
    """Create desktop application entry."""
    python_cmd = get_python_cmd(venv_path)

    # Create launcher script
    launcher_path = install_dir / "launch_agentos.sh"
    launcher_content = f"""#!/bin/bash
cd "{install_dir}"
{python_cmd} -m agentos.agentos app
"""
    launcher_path.write_text(launcher_content)
    os.chmod(launcher_path, 0o755)

    # Create desktop entry
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    icon_path = install_dir / "assets" / "agentos-logo.png"
    if not icon_path.exists():
        icon_path = "utilities-terminal"  # Fallback icon

    desktop_file = desktop_dir / "agentos.desktop"
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=AgentOS
Comment=Production AI Agent Runtime
Exec={launcher_path}
Icon={icon_path}
Terminal=true
Categories=Development;Utility;
Keywords=ai;agent;llm;automation;
StartupNotify=true
"""
    desktop_file.write_text(desktop_content)
    os.chmod(desktop_file, 0o755)

    print_success("Desktop entry created")


def create_systemd_service(install_dir, venv_path=None):
    """Create systemd service file (optional)."""
    python_cmd = get_python_cmd(venv_path)

    service_content = f"""[Unit]
Description=AgentOS - Production AI Agent Runtime
After=network.target

[Service]
Type=simple
User={os.environ.get("USER", "root")}
WorkingDirectory={install_dir}
ExecStart={python_cmd} -m agentos.agentos web --host 0.0.0.0 --port 5000
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

    service_file = install_dir / "agentos.service"
    service_file.write_text(service_content)

    print_success(f"Systemd service file created: {service_file}")
    print(f"  To install as system service:")
    print(f"    sudo cp {service_file} /etc/systemd/system/")
    print(f"    sudo systemctl daemon-reload")
    print(f"    sudo systemctl enable --now agentos")


def main():
    print(f"\n{Colors.BOLD}{'=' * 50}")
    print("       AgentOS Installer - Linux")
    print(f"{'=' * 50}{Colors.END}\n")

    # Parse arguments
    use_venv = "--no-venv" not in sys.argv
    skip_api_keys = "--skip-api-keys" in sys.argv

    # Check Python version
    print_step("Checking Python version...")
    check_python()

    # Check system dependencies
    check_system_deps()

    # Determine source directory (where this script is located)
    source_dir = Path(__file__).parent.resolve()

    # Verify it's a valid AgentOS installation
    if not (source_dir / "agentos").is_dir():
        print_error("Invalid AgentOS source directory")
        print(f"Expected to find 'agentos' folder in: {source_dir}")
        sys.exit(1)

    print_success(f"Source directory: {source_dir}")

    # Setup installation directory
    install_dir = Path.home() / ".agentos"
    install_dir.mkdir(parents=True, exist_ok=True)

    # Create symlink to source or copy
    source_link = install_dir / "source"
    if source_link.exists():
        if source_link.is_symlink():
            source_link.unlink()
        else:
            shutil.rmtree(source_link)

    try:
        source_link.symlink_to(source_dir)
    except Exception:
        print_warning("Could not create symlink, copying files...")
        shutil.copytree(source_dir, source_link, dirs_exist_ok=True)

    # Create virtual environment if requested
    venv_path = None
    if use_venv:
        venv_path = create_virtual_env(install_dir)

    # Install packages
    install_packages(source_dir, venv_path)

    # Configure API keys
    if not skip_api_keys:
        configure_api_keys(source_dir)

    # Create CLI wrapper
    create_cli_wrapper(source_dir, venv_path)

    # Create desktop entry
    create_desktop_entry(source_dir, venv_path)

    # Create systemd service file
    create_systemd_service(source_dir, venv_path)

    # Create data directories
    (install_dir / "logs").mkdir(exist_ok=True)
    (install_dir / "data").mkdir(exist_ok=True)

    # Print completion message
    print(f"\n{Colors.GREEN}{'=' * 50}")
    print("       Installation Complete!")
    print(f"{'=' * 50}{Colors.END}\n")

    print(f"{Colors.BOLD}Quick Start:{Colors.END}")
    print(f"  agentos --help        # Show help")
    print(f"  agentos chat          # Start chat mode")
    print(f"  agentos run agent.yaml --task 'your task'")
    print(f"  agentos web           # Start web UI")
    print()
    print(f"{Colors.BOLD}Installation Directory:{Colors.END} {install_dir}")
    print(f"{Colors.BOLD}Source Directory:{Colors.END} {source_dir}")
    if venv_path:
        print(f"{Colors.BOLD}Virtual Environment:{Colors.END} {venv_path}")
    print()
    print(f"Documentation: {source_dir / 'README.md'}")
    print(f"Configuration: {source_dir / '.env'}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)
