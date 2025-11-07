#!/usr/bin/env python3
"""AgentOS Uninstaller"""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    print("=== AgentOS Uninstaller ===\n")
    
    response = input("Are you sure you want to uninstall AgentOS? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Uninstall cancelled.")
        return
    
    # Uninstall pip package
    print("\nUninstalling AgentOS package...")
    subprocess.run(f"{sys.executable} -m pip uninstall -y agentos", shell=True)
    
    # Remove installation directory
    install_dir = Path.home() / ".agentos"
    if install_dir.exists():
        print(f"Removing {install_dir}...")
        shutil.rmtree(install_dir)
    
    # Remove desktop entry
    desktop_file = Path.home() / ".local" / "share" / "applications" / "agentos.desktop"
    if desktop_file.exists():
        print("Removing application menu entry...")
        desktop_file.unlink()
    
    print("\n✅ AgentOS uninstalled successfully!")


if __name__ == "__main__":
    main()
