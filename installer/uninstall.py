#!/usr/bin/env python3
"""AgentOS Uninstaller"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows Unicode issues
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


def main():
    print("=== 🤖 AgentOS Uninstaller ===\n")

    try:
        response = input("Are you sure you want to uninstall AgentOS? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Uninstall cancelled.")
            return
    except (EOFError, KeyboardInterrupt):
        print("\nUninstall cancelled.")
        return

    is_windows = platform.system().lower() == "windows"

    # Uninstall pip package
    print("\nUninstalling AgentOS package...")
    subprocess.run(f"{sys.executable} -m pip uninstall -y agentos", shell=True)

    # Remove installation directory
    install_dir = Path.home() / ".agentos"
    if install_dir.exists():
        print(f"Removing {install_dir}...")
        try:
            if is_windows:
                # Use Windows rmdir command to handle Git files
                subprocess.run(f'rmdir /s /q "{install_dir}"', shell=True, check=False)
            else:
                shutil.rmtree(install_dir)
        except Exception as e:
            print(f"Warning: Could not remove some files: {e}")
            print("You may need to manually delete the .agentos folder")

    # Remove menu entry
    if is_windows:
        shortcut_file = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "AgentOS.bat"
        if shortcut_file.exists():
            print("Removing Start Menu shortcut...")
            shortcut_file.unlink()
    else:
        desktop_file = Path.home() / ".local" / "share" / "applications" / "agentos.desktop"
        if desktop_file.exists():
            print("Removing application menu entry...")
            desktop_file.unlink()

    print("\n✅ AgentOS uninstalled successfully!")


if __name__ == "__main__":
    main()
