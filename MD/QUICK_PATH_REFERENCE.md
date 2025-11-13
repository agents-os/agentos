# AgentOS Path Resolution - Quick Reference

## TL;DR

AgentOS now works from **any directory**. Just run commands normally:

```bash
# Works from anywhere
agentos run default.yaml --task "your task"
agentos ui
agentos ps
```

## Common Scenarios

### Scenario 1: Run Agent from Home Directory
```bash
cd ~
agentos run default.yaml --task "create a Python script"
# ✅ Works! Finds default.yaml from project or examples
```

### Scenario 2: Run Agent from /tmp
```bash
cd /tmp
agentos run my-agent.yaml --task "analyze data"
# ✅ Works! Searches multiple locations
```

### Scenario 3: Use Absolute Path
```bash
agentos run /full/path/to/my-agent.yaml --task "your task"
# ✅ Works! Direct path always works
```

### Scenario 4: Use Relative Path
```bash
agentos run ./configs/my-agent.yaml --task "your task"
# ✅ Works! Relative to current directory
```

### Scenario 5: Launch Web UI from Anywhere
```bash
cd /any/directory
agentos ui
# ✅ Works! Templates found automatically
```

## Search Locations

When you run `agentos run my-agent.yaml`, it searches:

1. `./my-agent.yaml` (current directory)
2. `~/my-agent.yaml` (home directory)
3. `/path/to/agentos/my-agent.yaml` (project root)
4. `/path/to/agentos/examples/my-agent.yaml` (examples)

**First match wins!**

## File Organization

### Recommended Structure
```
~/.agentos/
├── runtime.db          # Database (auto-created)
├── logs/               # Agent logs (auto-created)
└── manifests/          # Your manifests (optional)
    ├── my-agent.yaml
    ├── data-agent.yaml
    └── scheduler-agent.yaml
```

### Create Manifests Here
```bash
# Store manifests in home directory
mkdir -p ~/.agentos/manifests
cp my-agent.yaml ~/.agentos/manifests/

# Run from anywhere
agentos run my-agent.yaml --task "your task"
```

## Troubleshooting

### Problem: "Manifest not found"

**Solution 1**: Use absolute path
```bash
agentos run /full/path/to/manifest.yaml --task "your task"
```

**Solution 2**: Move to searchable location
```bash
cp my-agent.yaml ~/.agentos/
agentos run my-agent.yaml --task "your task"
```

**Solution 3**: Check file exists
```bash
ls -la my-agent.yaml
```

### Problem: Web UI shows template errors

**Solution**: Reinstall or verify installation
```bash
pip install --upgrade agentos
```

### Problem: Can't find examples

**Solution**: Check examples directory
```bash
python -c "from agentos.core import path_resolver; print(path_resolver.get_examples_dir())"
```

## Command Reference

### Run Agent
```bash
# Simple name (searches multiple locations)
agentos run default.yaml --task "your task"

# Absolute path
agentos run /full/path/to/manifest.yaml --task "your task"

# Relative path
agentos run ./configs/manifest.yaml --task "your task"
```

### List Agents
```bash
agentos ps
# Works from any directory
```

### View Logs
```bash
agentos logs <agent-id>
# Works from any directory
```

### Launch Web UI
```bash
agentos ui
# Works from any directory
```

### Launch Desktop App
```bash
agentos app
# Works from any directory
```

### Create Manifest
```bash
agentos init my-agent.yaml
# Creates in current directory
```

### Schedule Agent
```bash
agentos schedule
# Works from any directory
```

## Environment Variables

### Optional Configuration
```bash
# Set custom secret key
export AGENTOS_SECRET_KEY="your-secret-key"

# Set Flask environment
export FLASK_ENV="production"

# Set API keys
export OPENAI_API_KEY="sk-..."
export CLAUDE_API_KEY="sk-..."
export GEMINI_API_KEY="..."
```

## Data Locations

### Always Centralized
```
~/.agentos/
├── runtime.db          # Agent database
└── logs/               # Agent execution logs
    ├── agent1_abc123.log
    ├── agent2_def456.log
    └── ...
```

**Note**: These locations are **not affected** by your working directory.

## Best Practices

### ✅ DO

```bash
# Store manifests in one place
mkdir -p ~/.agentos/manifests
cp *.yaml ~/.agentos/manifests/

# Use simple names
agentos run my-agent.yaml --task "your task"

# Run from any directory
cd /tmp && agentos run my-agent.yaml --task "your task"

# Use absolute paths in scripts
#!/bin/bash
MANIFEST="$HOME/.agentos/manifests/my-agent.yaml"
agentos run "$MANIFEST" --task "your task"
```

### ❌ DON'T

```bash
# Don't scatter manifests everywhere
# Hard to track and maintain

# Don't use relative paths in scripts
# May fail depending on where script is run
#!/bin/bash
agentos run ./my-agent.yaml --task "your task"  # ❌ Bad

# Don't assume working directory
# Always use absolute paths or simple names
```

## Examples

### Example 1: Simple Task
```bash
# From anywhere
agentos run default.yaml --task "create a Python hello world"
```

### Example 2: Data Analysis
```bash
# From anywhere
agentos run data-agent.yaml --task "analyze sales data"
```

### Example 3: Scheduled Task
```bash
# Create manifest with schedule
cat > ~/.agentos/manifests/daily-report.yaml << EOF
name: daily_reporter
model_provider: github
model_version: openai/gpt-4o-mini
time: 9  # Run daily at 9 AM
EOF

# Run from anywhere
agentos run daily-report.yaml --task "generate daily report"
```

### Example 4: Web UI
```bash
# From any directory
cd /tmp
agentos ui
# Access at http://localhost:5000
```

## Getting Help

### Check Path Resolution
```bash
python -c "from agentos.core import path_resolver; print(path_resolver.find_all_manifests())"
```

### View Project Root
```bash
python -c "from agentos.core import path_resolver; print(path_resolver.get_project_root())"
```

### View Current Directory
```bash
pwd
```

### List Available Manifests
```bash
# In project root
ls *.yaml examples/*.yaml

# In home directory
ls ~/.agentos/*.yaml ~/.agentos/manifests/*.yaml 2>/dev/null
```

## Summary

| Feature | Status |
|---------|--------|
| Run from any directory | ✅ Works |
| Automatic file discovery | ✅ Works |
| Absolute paths | ✅ Works |
| Relative paths | ✅ Works |
| Web UI from anywhere | ✅ Works |
| Centralized database | ✅ Works |
| Centralized logs | ��� Works |
| Backward compatible | ✅ Yes |

**You're all set!** AgentOS now works seamlessly from any directory.
