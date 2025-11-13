# AgentOS Path Resolution Guide

## Overview

AgentOS now includes comprehensive path resolution capabilities that allow it to work correctly from any directory. This guide explains how path resolution works and how to use it effectively.

## Path Resolution System

### How It Works

AgentOS uses a multi-location search strategy to find files and resources:

1. **Absolute Paths**: If you provide an absolute path, it's used directly
2. **Current Working Directory**: Files in the directory where you run the command
3. **Home Directory**: Files in your home directory (`~`)
4. **Project Root**: Files in the AgentOS installation directory
5. **Examples Directory**: Sample manifests in the examples folder

### Search Order for Manifest Files

When you run:
```bash
agentos run my-agent.yaml --task "your task"
```

AgentOS searches for `my-agent.yaml` in this order:
1. `/absolute/path/to/my-agent.yaml` (if absolute path provided)
2. `./my-agent.yaml` (current working directory)
3. `~/my-agent.yaml` (home directory)
4. `/path/to/agentos/installation/my-agent.yaml` (project root)
5. `/path/to/agentos/installation/examples/my-agent.yaml` (examples)

## Usage Examples

### Running from Different Directories

**From Project Root:**
```bash
cd /media/abdulhadi/New\ Volume/AbdulHadi/Projects/AgentOS
agentos run default.yaml --task "create a Python script"
```

**From Home Directory:**
```bash
cd ~
agentos run default.yaml --task "create a Python script"
```

**From Any Directory:**
```bash
cd /tmp
agentos run default.yaml --task "create a Python script"
```

All three commands will work because AgentOS searches multiple locations.

### Using Absolute Paths

```bash
agentos run /full/path/to/my-agent.yaml --task "your task"
```

### Using Relative Paths

```bash
# From current directory
agentos run ./configs/my-agent.yaml --task "your task"

# From subdirectory
agentos run ../my-agent.yaml --task "your task"
```

## Path Resolver Module

### Location
`agentos/core/path_resolver.py`

### Key Functions

#### `resolve_manifest_path(manifest_name: str) -> Optional[Path]`
Resolves a manifest file path from multiple locations.

```python
from agentos.core.path_resolver import resolve_manifest_path

path = resolve_manifest_path("my-agent.yaml")
if path:
    print(f"Found at: {path}")
else:
    print("Manifest not found")
```

#### `get_project_root() -> Path`
Returns the AgentOS project root directory.

```python
from agentos.core.path_resolver import get_project_root

root = get_project_root()
print(f"Project root: {root}")
```

#### `get_examples_dir() -> Path`
Returns the examples directory.

```python
from agentos.core.path_resolver import get_examples_dir

examples = get_examples_dir()
print(f"Examples: {examples}")
```

#### `find_all_manifests() -> list`
Finds all manifest files in searchable locations.

```python
from agentos.core.path_resolver import find_all_manifests

manifests = find_all_manifests()
for manifest in manifests:
    print(f"Found: {manifest}")
```

#### `get_working_directory() -> Path`
Returns the current working directory.

```python
from agentos.core.path_resolver import get_working_directory

cwd = get_working_directory()
print(f"Current directory: {cwd}")
```

## Configuration Files

### Default Locations

AgentOS looks for configuration files in:

1. **Current Working Directory**
   ```
   ./default.yaml
   ./my-agent.yaml
   ```

2. **Home Directory**
   ```
   ~/.agentos/default.yaml
   ~/.agentos/my-agent.yaml
   ```

3. **Project Root**
   ```
   /path/to/agentos/default.yaml
   /path/to/agentos/examples/default.yaml
   ```

### Creating Manifests in Different Locations

**In Current Directory:**
```bash
agentos init my-agent.yaml
```

**In Home Directory:**
```bash
agentos init ~/.agentos/my-agent.yaml
```

**In Project Directory:**
```bash
agentos init /path/to/agentos/my-agent.yaml
```

## Database and Logs

### Database Location
- **Always**: `~/.agentos/runtime.db`
- **Not affected by working directory**

### Log Files
- **Always**: `~/.agentos/logs/`
- **Not affected by working directory**

This ensures all agent data is centralized regardless of where you run commands.

## Web UI and Desktop App

### Template and Static Files

The web UI automatically finds templates and static files from:

1. Project root: `/path/to/agentos/templates/`
2. Project root: `/path/to/agentos/static/`

These are resolved using the path resolver, so the UI works from any directory.

### Running Web UI from Different Directories

```bash
# From project root
cd /path/to/agentos
agentos ui

# From home directory
cd ~
agentos ui

# From any directory
cd /tmp
agentos ui
```

All commands will work correctly.

## Troubleshooting

### "Manifest file not found" Error

**Problem**: You get an error like:
```
❌ Manifest file not found: my-agent.yaml
Searched in: /current/directory/my-agent.yaml
```

**Solutions**:

1. **Check file exists**:
   ```bash
   ls -la my-agent.yaml
   ```

2. **Use absolute path**:
   ```bash
   agentos run /full/path/to/my-agent.yaml --task "your task"
   ```

3. **Move file to searchable location**:
   ```bash
   cp my-agent.yaml ~/.agentos/
   agentos run my-agent.yaml --task "your task"
   ```

4. **Check current directory**:
   ```bash
   pwd
   ls *.yaml
   ```

### "Templates not found" Error

**Problem**: Web UI shows template errors.

**Solution**: The path resolver automatically finds templates. If this fails:

1. Verify AgentOS installation:
   ```bash
   python -c "from agentos.core import path_resolver; print(path_resolver.get_templates_dir())"
   ```

2. Check templates exist:
   ```bash
   ls -la /path/to/agentos/templates/
   ```

### "Examples not found" Error

**Problem**: Example manifests aren't showing in web UI.

**Solution**:

1. Check examples directory:
   ```bash
   ls -la /path/to/agentos/examples/
   ```

2. Verify path resolver finds them:
   ```bash
   python -c "from agentos.core import path_resolver; print(path_resolver.get_examples_dir())"
   ```

## Best Practices

### 1. Use Consistent Manifest Locations

**Good**:
```bash
# Store all manifests in one place
mkdir -p ~/.agentos/manifests
cp my-agent.yaml ~/.agentos/manifests/
agentos run my-agent.yaml --task "your task"
```

**Avoid**:
```bash
# Scattered manifests in different directories
# Hard to track and maintain
```

### 2. Use Absolute Paths for Scripts

**Good**:
```bash
#!/bin/bash
MANIFEST="/path/to/my-agent.yaml"
agentos run "$MANIFEST" --task "your task"
```

**Avoid**:
```bash
#!/bin/bash
# Relative paths may fail depending on where script is run
agentos run my-agent.yaml --task "your task"
```

### 3. Document Manifest Locations

**Good**:
```yaml
# my-agent.yaml
# Location: ~/.agentos/manifests/my-agent.yaml
# Run with: agentos run my-agent.yaml --task "your task"

name: my_assistant
model_provider: github
model_version: openai/gpt-4o-mini
```

### 4. Use Environment Variables

**Good**:
```bash
export AGENTOS_MANIFEST_DIR="$HOME/.agentos/manifests"
agentos run "$AGENTOS_MANIFEST_DIR/my-agent.yaml" --task "your task"
```

## Advanced Usage

### Finding All Manifests Programmatically

```python
from agentos.core.path_resolver import find_all_manifests

manifests = find_all_manifests()
for manifest in manifests:
    print(f"Manifest: {manifest}")
    print(f"  Name: {manifest.name}")
    print(f"  Parent: {manifest.parent}")
```

### Checking Path Resolution

```python
from agentos.core.path_resolver import resolve_manifest_path

# Test resolution
test_files = [
    "default.yaml",
    "my-agent.yaml",
    "examples/quick-start.yaml"
]

for filename in test_files:
    path = resolve_manifest_path(filename)
    if path:
        print(f"✓ {filename} -> {path}")
    else:
        print(f"✗ {filename} not found")
```

### Custom Path Resolution

```python
from pathlib import Path
from agentos.core.path_resolver import resolve_manifest_path, get_project_root

# Add custom search location
custom_dir = Path("/my/custom/manifests")

# Check custom location
if (custom_dir / "my-agent.yaml").exists():
    manifest_path = custom_dir / "my-agent.yaml"
else:
    # Fall back to default resolution
    manifest_path = resolve_manifest_path("my-agent.yaml")
```

## Summary

AgentOS now provides robust path resolution that:

✅ Works from any directory  
✅ Searches multiple locations automatically  
✅ Supports absolute and relative paths  
✅ Centralizes database and logs  
✅ Finds templates and static files automatically  
✅ Provides programmatic access via path_resolver module  

This makes AgentOS more flexible and user-friendly, whether you're running it from the project directory, home directory, or anywhere else on your system.
