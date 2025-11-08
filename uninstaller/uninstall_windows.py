#!/usr/bin/env python3
"""AgentOS Uninstaller - Windows

Purchase: https://junaidahmed65.gumroad.com/l/spfzuo
Repository: https://github.com/agents-os/agentos
"""

import shutil
import subprocess
import sys
from pathlib import Path


print("=== AgentOS Uninstaller (Windows) ===\n")

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

# Remove Start Menu shortcut
shortcut_file = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "AgentOS.bat"
if shortcut_file.exists():
    print("Removing Start Menu shortcut...")
    shortcut_file.unlink()

print("\n✅ AgentOS uninstalled successfully!")
