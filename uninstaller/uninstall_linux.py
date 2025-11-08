#!/usr/bin/env python3
"""AgentOS Uninstaller - Linux

Purchase: https://junaidahmed65.gumroad.com/l/spfzuo
Repository: https://github.com/agents-os/agentos
"""

import shutil
import subprocess
import sys
from pathlib import Path


print("=== AgentOS Uninstaller (Linux) ===\n")

response = input("Are you sure you want to uninstall AgentOS? (yes/no): ")
if response.lower() not in ["yes", "y"]:
    print("Uninstall cancelled.")
    sys.exit(0)

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

# Remove icon
icon_file = Path.home() / ".local" / "share" / "icons" / "agentos-logo.png"
if icon_file.exists():
    icon_file.unlink()

print("\n✅ AgentOS uninstalled successfully!")
