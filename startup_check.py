#!/usr/bin/env python3
"""
AgentOS Startup Validation Script
Validates environment and dependencies before starting
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check required Python packages"""
    required = [
        'flask',
        'yaml',
        'rich',
        'sqlite3',
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not found")
            missing.append(package)
    
    return len(missing) == 0

def check_directories():
    """Check required directories exist"""
    home = Path.home()
    agentos_dir = home / ".agentos"
    logs_dir = agentos_dir / "logs"
    
    try:
        agentos_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directories: {agentos_dir}")
        return True
    except Exception as e:
        print(f"❌ Failed to create directories: {e}")
        return False

def check_database():
    """Check database connectivity"""
    try:
        import db
        agents = db.list_agents()
        print(f"✅ Database connected ({len(agents)} agents)")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_api_keys():
    """Check for at least one API key"""
    api_keys = [
        'GIT_HUB_TOKEN',
        'OPENAI_API_KEY',
        'CLAUDE_API_KEY',
        'GEMINI_API_KEY',
        'COHERE_API_KEY',
    ]
    
    found = []
    for key in api_keys:
        if os.environ.get(key):
            found.append(key)
            print(f"✅ {key} configured")
    
    if not found:
        print("⚠️  No API keys found. Set at least one LLM provider key.")
        return False
    
    return True

def check_config():
    """Check configuration"""
    secret_key = os.environ.get('AGENTOS_SECRET_KEY', 'default')
    if secret_key == 'default' or secret_key == 'change-this-in-production':
        print("⚠️  AGENTOS_SECRET_KEY using default value")
        return False
    
    print("✅ Configuration validated")
    return True

def check_ports():
    """Check if required ports are available"""
    import socket
    
    def is_port_available(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
    
    port = 5000
    if is_port_available(port):
        print(f"✅ Port {port} available")
        return True
    else:
        print(f"⚠️  Port {port} already in use")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("AgentOS Startup Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Database", check_database),
        ("API Keys", check_api_keys),
        ("Configuration", check_config),
        ("Ports", check_ports),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 40)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed: {e}")
            results.append(False)
    
    print()
    print("=" * 60)
    
    if all(results):
        print("✅ All checks passed! AgentOS is ready to start.")
        print("=" * 60)
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"⚠️  {failed} check(s) failed. Please fix issues before starting.")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
