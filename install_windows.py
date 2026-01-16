#!/usr/bin/env python3
"""
AgentOS Installer - Windows
===========================

This script installs AgentOS on Windows systems.

Usage:
    python install_windows.py [--no-venv] [--skip-api-keys]

Options:
    --no-venv       Install globally instead of virtual environment
    --skip-api-keys Skip API key configuration prompt

Repository: https://github.com/agents-os/agentos
"""

import ctypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows Unicode issues early
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Enable ANSI escape codes on Windows 10+
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_step(msg):
    print(f"{Colors.BLUE}==>{Colors.END} {msg}")


def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}[X]{Colors.END} {msg}")


def run_cmd(cmd, cwd=None, check=True, capture=True):
    """Execute a shell command."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=capture,
            text=True,
            encoding="utf-8",
            errors="replace",
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


def is_admin():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


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
    """Check system dependencies."""
    print_step("Checking system dependencies...")

    # Check for pip
    result = run_cmd(f'"{sys.executable}" -m pip --version', check=False)
    if result is None or result.returncode != 0:
        print_error("pip not found. Please reinstall Python with pip enabled.")
        sys.exit(1)
    print_success("pip available")

    # Check for git (optional)
    result = run_cmd("where git", check=False)
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
            shutil.rmtree(venv_path, ignore_errors=True)
        else:
            return venv_path

    print_step("Creating virtual environment...")
    result = run_cmd(f'"{sys.executable}" -m venv "{venv_path}"')
    if result is None:
        print_error("Failed to create virtual environment")
        print_warning("Trying without virtual environment...")
        return None

    print_success(f"Virtual environment created at {venv_path}")
    return venv_path


def get_pip_cmd(venv_path=None):
    """Get the pip command for the environment."""
    if venv_path:
        pip_path = venv_path / "Scripts" / "pip.exe"
        return f'"{pip_path}"'
    return f'"{sys.executable}" -m pip'


def get_python_cmd(venv_path=None):
    """Get the python command for the environment."""
    if venv_path:
        python_path = venv_path / "Scripts" / "python.exe"
        return f'"{python_path}"'
    return f'"{sys.executable}"'


def install_packages(source_dir, venv_path=None):
    """Install AgentOS and dependencies."""
    pip_cmd = get_pip_cmd(venv_path)

    print_step("Upgrading pip...")
    run_cmd(f"{pip_cmd} install --upgrade pip", check=False)

    print_step("Installing core dependencies...")
    run_cmd(f"{pip_cmd} install wheel setuptools", check=False)

    print_step("Installing dependencies...")
    req_file = source_dir / "requirements.txt"
    if req_file.exists():
        result = run_cmd(f'{pip_cmd} install -r "{req_file}"')
        if result is None:
            print_warning("Some dependencies may have failed to install")

    print_step("Installing AgentOS...")
    result = run_cmd(f'{pip_cmd} install -e "{source_dir}"')
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
    env_content = "# AgentOS API Keys\r\n"
    env_content += "# Add your API keys here\r\n\r\n"

    for key in api_keys:
        if key in configured_keys:
            env_content += f"{key}={configured_keys[key]}\r\n"
        else:
            env_content += f"# {key}=your_key_here\r\n"

    env_file.write_text(env_content, encoding="utf-8")

    if configured_keys:
        print_success(f"API keys saved to {env_file}")
    else:
        print_warning(f"No API keys configured. Edit {env_file} later.")


def create_batch_scripts(install_dir, source_dir, venv_path=None):
    """Create batch scripts for Windows."""
    python_cmd = get_python_cmd(venv_path).strip('"')

    # Main CLI batch file
    cli_batch = install_dir / "agentos.bat"
    cli_content = f"""@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
cd /d "{source_dir}"
"{python_cmd}" -m agentos.agentos %*
"""
    cli_batch.write_text(cli_content, encoding="utf-8")
    print_success(f"CLI script: {cli_batch}")

    # Chat mode launcher
    chat_batch = install_dir / "agentos-chat.bat"
    chat_content = f"""@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
cd /d "{source_dir}"
"{python_cmd}" -m agentos.agentos chat
pause
"""
    chat_batch.write_text(chat_content, encoding="utf-8")

    # Web UI launcher
    web_batch = install_dir / "agentos-web.bat"
    web_content = f"""@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
cd /d "{source_dir}"
echo Starting AgentOS Web UI at http://localhost:5000
"{python_cmd}" -m agentos.agentos web --host 127.0.0.1 --port 5000
pause
"""
    web_batch.write_text(web_content, encoding="utf-8")

    return cli_batch


def create_start_menu_shortcut(install_dir, source_dir, venv_path=None):
    """Create Start Menu shortcuts."""
    python_cmd = get_python_cmd(venv_path).strip('"')

    # Start Menu Programs folder
    start_menu = (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "AgentOS"
    )
    start_menu.mkdir(parents=True, exist_ok=True)

    # Chat launcher
    chat_bat = start_menu / "AgentOS Chat.bat"
    chat_content = f"""@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
cd /d "{source_dir}"
"{python_cmd}" -m agentos.agentos chat
"""
    chat_bat.write_text(chat_content, encoding="utf-8")

    # Web UI launcher
    web_bat = start_menu / "AgentOS Web UI.bat"
    web_content = f"""@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
cd /d "{source_dir}"
start http://localhost:5000
"{python_cmd}" -m agentos.agentos web --host 127.0.0.1 --port 5000
"""
    web_bat.write_text(web_content, encoding="utf-8")

    # Command Prompt launcher
    cmd_bat = start_menu / "AgentOS Command Prompt.bat"
    cmd_content = f"""@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
cd /d "{source_dir}"
set PATH={install_dir};%PATH%
echo AgentOS Command Prompt
echo Type 'agentos --help' for available commands
echo.
cmd /k
"""
    cmd_bat.write_text(cmd_content, encoding="utf-8")

    print_success(f"Start Menu shortcuts created in: {start_menu}")


def add_to_path(install_dir):
    """Add AgentOS to user PATH (requires restart)."""
    print_step("Adding to PATH...")

    try:
        import winreg

        # Open user environment variables
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS
        )

        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except WindowsError:
            current_path = ""

        install_str = str(install_dir)
        if install_str not in current_path:
            new_path = f"{current_path};{install_str}" if current_path else install_str
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            print_success("Added to user PATH")
            print_warning("Restart your terminal for PATH changes to take effect")
        else:
            print_success("Already in PATH")

        winreg.CloseKey(key)

        # Notify Windows of environment change
        import ctypes

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        ctypes.windll.user32.SendMessageW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment"
        )

    except Exception as e:
        print_warning(f"Could not add to PATH: {e}")
        print(f"  Manually add this to your PATH: {install_dir}")


def create_uninstaller(install_dir, source_dir):
    """Create uninstaller script."""
    uninstall_bat = install_dir / "uninstall.bat"
    uninstall_content = f"""@echo off
echo AgentOS Uninstaller
echo ===================
echo.
echo This will remove AgentOS from your system.
echo.
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto :cancel

echo.
echo Removing Start Menu shortcuts...
rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\AgentOS" 2>nul

echo Removing installation directory...
rmdir /s /q "{install_dir}" 2>nul

echo.
echo AgentOS has been uninstalled.
echo Note: You may need to manually remove AgentOS from your PATH.
pause
goto :eof

:cancel
echo Uninstallation cancelled.
pause
"""
    uninstall_bat.write_text(uninstall_content, encoding="utf-8")
    print_success(f"Uninstaller created: {uninstall_bat}")


def main():
    print(f"\n{Colors.BOLD}{'=' * 50}")
    print("       AgentOS Installer - Windows")
    print(f"{'=' * 50}{Colors.END}\n")

    # Parse arguments
    use_venv = "--no-venv" not in sys.argv
    skip_api_keys = "--skip-api-keys" in sys.argv

    # Check if running as admin (informational)
    if is_admin():
        print_warning("Running as Administrator")

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

    print_success(f"Installation directory: {install_dir}")

    # Create symlink or copy source
    source_link = install_dir / "source"
    if source_link.exists():
        if source_link.is_symlink() or source_link.is_junction():
            source_link.unlink()
        else:
            shutil.rmtree(source_link, ignore_errors=True)

    # On Windows, try junction first, then copy
    try:
        run_cmd(f'mklink /J "{source_link}" "{source_dir}"', check=True)
        print_success("Created junction to source")
    except Exception:
        print_warning("Could not create junction, copying files...")
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

    # Create batch scripts
    cli_batch = create_batch_scripts(install_dir, source_dir, venv_path)

    # Create Start Menu shortcuts
    create_start_menu_shortcut(install_dir, source_dir, venv_path)

    # Add to PATH
    add_to_path(install_dir)

    # Create uninstaller
    create_uninstaller(install_dir, source_dir)

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
    print(f'  agentos run agent.yaml --task "your task"')
    print(f"  agentos web           # Start web UI")
    print()
    print(f"{Colors.BOLD}Shortcuts:{Colors.END}")
    print(f"  - Find 'AgentOS' in your Start Menu")
    print(f"  - Or run: {cli_batch}")
    print()
    print(f"{Colors.BOLD}Installation Directory:{Colors.END} {install_dir}")
    print(f"{Colors.BOLD}Source Directory:{Colors.END} {source_dir}")
    if venv_path:
        print(f"{Colors.BOLD}Virtual Environment:{Colors.END} {venv_path}")
    print()
    print(f"Documentation: {source_dir / 'README.md'}")
    print(f"Configuration: {source_dir / '.env'}")
    print()
    print_warning("Restart your terminal for PATH changes to take effect!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        import traceback

        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
