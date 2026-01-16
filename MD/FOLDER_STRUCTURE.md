# AgentOS Folder Structure

## Overview

All Python modules have been organized into a logical folder structure for better maintainability and clarity.

## Structure

```
AgentOS/
├── agentos.py                    # Main CLI entry point
├── setup.py                      # Package setup
├── production_config.py          # Production configuration
├── startup_check.py              # Startup validation
│
├── agentos/                      # Main package
│   ├── __init__.py
│   │
│   ├── cli/                      # CLI layer
│   │   ├── __init__.py
│   │   ├── cli_parser.py         # Argument parsing
│   │   ├── cli_helpers.py        # Helper utilities
│   │   ├── cli_commands.py       # Command aggregator
│   │   ├── cli_cmd_basic.py      # Basic commands (run, ps, logs)
│   │   ├── cli_cmd_schedule.py   # Schedule management
│   │   ├── cli_cmd_ui.py         # Web/desktop UI
│   │   └── cli_cmd_utils.py      # Utility commands (stop, prune)
│   │
│   ├── agent/                    # Agent execution layer
│   │   ├── __init__.py
│   │   ├── cli_agent.py          # Main agent loop
│   │   ├── agent_planner.py      # Planning logic
│   │   └── agent_executor.py     # Command execution
│   │
│   ├── llm/                      # LLM integration layer
│   │   ├── __init__.py
│   │   ├── answerer.py           # Main LLM interface
│   │   └── llm_providers.py      # Provider implementations
│   │
│   ├── database/                 # Database layer
│   │   ├── __init__.py
│   │   ├── db.py                 # Main database interface
│   │   ├── db_core.py            # Core operations
│   │   ├── db_agents.py          # Agent ops aggregator
│   │   ├── db_agent_ops.py       # Basic agent operations
│   │   ├── db_agent_cli.py       # CLI helpers
│   │   └── db_scheduler.py       # Scheduler operations
│   │
│   ├── web/                      # Web interface layer
│   │   ├── __init__.py
│   │   ├── web_ui.py             # Flask app
│   │   └── web_routes.py         # Route handlers
│   │
│   ├── core/                     # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration
│   │   ├── utils.py              # Utilities
│   │   ├── threader.py           # Threading
│   │   ├── isolate.py            # Docker isolation
│   │   ├── scheduler.py          # Agent scheduler
│   │   ├── retry.py              # Retry logic with exponential backoff
│   │   ├── security.py           # Security validation & command filtering
│   │   ├── chat_history.py       # Persistent chat storage (SQLite)
│   │   ├── shutdown.py           # Graceful shutdown handling
│   │   ├── docker_sandbox.py     # Enhanced Docker sandbox
│   │   └── process_manager.py    # Real-time process monitoring
│   │
│   └── mcp/                      # Model Context Protocol
│       ├── __init__.py
│       ├── client.py             # MCP client
│       └── tools.py              # MCP tools
│
├── examples/                     # Example manifests
├── templates/                    # Web UI templates
├── static/                       # Web UI static files
└── MD/                           # Documentation
```

## Core Module Reference

### New Modules (v1.1.0)

| Module               | Purpose             | Key Classes/Functions                   |
| -------------------- | ------------------- | --------------------------------------- |
| `retry.py`           | Retry with backoff  | `RetryConfig`, `retry_with_backoff()`   |
| `security.py`        | Security validation | `validate_command()`, `SecurityContext` |
| `chat_history.py`    | Chat persistence    | `ChatHistoryManager`                    |
| `shutdown.py`        | Graceful shutdown   | `ShutdownManager`, `ShutdownContext`    |
| `docker_sandbox.py`  | Docker isolation    | `DockerSandbox`                         |
| `process_manager.py` | Process monitoring  | `ProcessMonitor`, `AgentLifecycle`      |

## Import Patterns

### From Root

```python
from agentos.cli.cli_commands import cmd_run
from agentos.database import db
from agentos.core import utils
```

### Within Package

```python
from agentos.agent.agent_planner import ask_llm
from agentos.llm.answerer import get_github_response
from agentos.database.db_core import init_db
```

## Benefits

1. **Clear Organization**: Each layer has its own folder
2. **Easy Navigation**: Find files by their purpose
3. **Better Imports**: Explicit import paths show dependencies
4. **Scalability**: Easy to add new modules to appropriate folders
5. **Testing**: Can test each layer independently

## Migration Notes

All imports have been updated to use the new folder structure. The main entry point (`agentos.py`) remains in the root for easy CLI access.
