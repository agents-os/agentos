# AgentOS API Reference

Complete API documentation for AgentOS core modules.

## Table of Contents

- [Retry Module](#retry-module)
- [Security Module](#security-module)
- [Chat History Module](#chat-history-module)
- [Shutdown Module](#shutdown-module)
- [Docker Sandbox Module](#docker-sandbox-module)
- [Process Manager Module](#process-manager-module)

---

## Retry Module

`agentos.core.retry`

Provides retry logic with exponential backoff for handling transient failures.

### Classes

#### `RetryConfig`

Configuration for retry behavior.

```python
from dataclasses import dataclass

@dataclass
class RetryConfig:
    max_retries: int = 3          # Maximum retry attempts
    initial_delay: float = 1.0     # Initial delay in seconds
    max_delay: float = 30.0        # Maximum delay cap
    exponential_base: float = 2.0  # Backoff multiplier
    jitter: bool = True            # Add randomness to delays
```

### Functions

#### `retry_with_backoff(config: RetryConfig)`

Decorator that adds retry logic to any function.

```python
from agentos.core.retry import retry_with_backoff, DEFAULT_LLM_RETRY

@retry_with_backoff(DEFAULT_LLM_RETRY)
def call_api():
    # Will retry on exception with exponential backoff
    return api.request()
```

#### `calculate_delay(attempt: int, config: RetryConfig) -> float`

Calculate delay for a specific retry attempt.

```python
from agentos.core.retry import calculate_delay, DEFAULT_LLM_RETRY

delay = calculate_delay(attempt=2, config=DEFAULT_LLM_RETRY)
# Returns delay in seconds with jitter applied
```

### Pre-configured Strategies

```python
from agentos.core.retry import (
    DEFAULT_LLM_RETRY,   # 3 retries, 1-30s delay
    AGGRESSIVE_RETRY,    # 5 retries, 0.5-60s delay
    GENTLE_RETRY,        # 2 retries, 2-10s delay
)
```

---

## Security Module

`agentos.core.security`

Security validation, command filtering, and input sanitization.

### Classes

#### `ValidationResult`

Result of a validation check.

```python
@dataclass
class ValidationResult:
    is_safe: bool
    message: str
    risk_level: str  # "safe", "warning", "blocked"
```

#### `ResourceLimits`

Per-agent resource constraints.

```python
@dataclass
class ResourceLimits:
    max_steps: int = 50
    timeout: int = 300
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
```

#### `SecurityContext`

Context manager for security tracking.

```python
from agentos.core.security import SecurityContext

with SecurityContext(agent_id="my_agent") as ctx:
    # All operations logged
    # Automatic cleanup on exit
    pass
```

### Functions

#### `validate_command(command: str) -> ValidationResult`

Check if a command is safe to execute.

```python
from agentos.core.security import validate_command

result = validate_command("rm -rf /")
if not result.is_safe:
    print(f"Blocked: {result.message}")
```

#### `validate_input(user_input: str) -> ValidationResult`

Check user input for injection patterns.

```python
from agentos.core.security import validate_input

result = validate_input("hello; rm -rf /")
# Returns ValidationResult(is_safe=False, ...)
```

#### `sanitize_input(user_input: str) -> str`

Remove potentially dangerous characters from input.

```python
from agentos.core.security import sanitize_input

safe = sanitize_input("hello $(whoami)")
# Returns "hello whoami"
```

#### `sanitize_path(path: str, workspace: str) -> str`

Ensure path stays within workspace boundaries.

```python
from agentos.core.security import sanitize_path

safe_path = sanitize_path("../../../etc/passwd", "/home/user/project")
# Raises SecurityError or returns normalized path within workspace
```

### Constants

```python
BLOCKED_COMMANDS = [
    "rm", "rmdir", "shred", "sudo", "su", "chmod", "chown",
    "dd", "mkfs", "fdisk", "format", "kill", "killall", "pkill",
    "reboot", "shutdown", "init", "nc", "netcat", ...
]

DANGEROUS_PATTERNS = [
    r"rm\s+(-rf?|--recursive)", r">\s*/dev/", r"chmod\s+777", ...
]

INJECTION_PATTERNS = [
    r";\s*", r"&&", r"\|\|", r"\|", r"\$\(", r"`", ...
]
```

---

## Chat History Module

`agentos.core.chat_history`

Persistent chat storage with SQLite backend.

### Class: `ChatHistoryManager`

```python
from agentos.core.chat_history import ChatHistoryManager

history = ChatHistoryManager(db_path="~/.agentos/chat_history.db")
```

### Methods

#### `create_conversation(agent_id: str, title: str = None, metadata: dict = None) -> str`

Create a new conversation and return its ID.

```python
conv_id = history.create_conversation(
    agent_id="assistant",
    title="Python Help",
    metadata={"topic": "file-io"}
)
```

#### `add_message(conversation_id: str, role: str, content: str, metadata: dict = None)`

Add a message to a conversation.

```python
history.add_message(conv_id, "user", "How do I read a file?")
history.add_message(conv_id, "assistant", "Use open() function...")
```

#### `get_messages(conversation_id: str, limit: int = None) -> List[dict]`

Retrieve messages from a conversation.

```python
messages = history.get_messages(conv_id, limit=10)
for msg in messages:
    print(f"{msg['role']}: {msg['content']}")
```

#### `search_messages(query: str, agent_id: str = None, limit: int = 50) -> List[dict]`

Search across all messages.

```python
results = history.search_messages("file", agent_id="assistant")
```

#### `get_context(conversation_id: str, max_messages: int = 10) -> List[dict]`

Get recent context for continuing a conversation.

```python
context = history.get_context(conv_id, max_messages=5)
# Returns last 5 messages formatted for LLM input
```

#### `export_conversation(conversation_id: str, filepath: str, format: str = "json")`

Export conversation to file.

```python
# Export as JSON
history.export_conversation(conv_id, "chat.json", format="json")

# Export as Markdown
history.export_conversation(conv_id, "chat.md", format="markdown")

# Export as plain text
history.export_conversation(conv_id, "chat.txt", format="text")
```

#### `delete_conversation(conversation_id: str)`

Delete a conversation and all its messages.

```python
history.delete_conversation(conv_id)
```

#### `list_conversations(agent_id: str = None) -> List[dict]`

List all conversations, optionally filtered by agent.

```python
conversations = history.list_conversations(agent_id="assistant")
```

---

## Shutdown Module

`agentos.core.shutdown`

Graceful shutdown handling with signal management.

### Class: `ShutdownManager` (Singleton)

```python
from agentos.core.shutdown import ShutdownManager

manager = ShutdownManager()
```

### Methods

#### `register_callback(callback: Callable, priority: int = 0)`

Register a cleanup function to run on shutdown.

```python
def cleanup_resources():
    print("Cleaning up...")

manager.register_callback(cleanup_resources, priority=10)
# Higher priority = runs first
```

#### `unregister_callback(callback: Callable)`

Remove a registered callback.

```python
manager.unregister_callback(cleanup_resources)
```

#### `graceful_shutdown(signum: int = None, frame = None)`

Trigger graceful shutdown (called automatically on signals).

```python
manager.graceful_shutdown()
```

#### `is_shutting_down() -> bool`

Check if shutdown is in progress.

```python
if manager.is_shutting_down():
    return  # Exit early
```

### Context Manager: `ShutdownContext`

```python
from agentos.core.shutdown import ShutdownContext

with ShutdownContext():
    # SIGTERM/SIGINT handled gracefully
    # Cleanup callbacks run on exit
    run_long_task()
```

---

## Docker Sandbox Module

`agentos.core.docker_sandbox`

Docker-based isolation for safe command execution.

### Class: `DockerSandbox`

```python
from agentos.core.docker_sandbox import DockerSandbox

sandbox = DockerSandbox(
    image="python:3.11-slim",     # Base image
    memory_limit="256m",          # Memory constraint
    cpu_quota=50000,              # CPU microseconds per period
    network_mode="none",          # Network isolation
    read_only=False,              # Read-only filesystem
    working_dir="/workspace",     # Working directory
    timeout=300,                  # Execution timeout
)
```

### Methods

#### `run_in_sandbox(command: str, env: dict = None) -> SandboxResult`

Execute a command in the sandbox.

```python
result = sandbox.run_in_sandbox("python script.py", env={"DEBUG": "1"})
print(result.stdout)
print(result.stderr)
print(result.exit_code)
```

#### `run_script(script: str, language: str = "python") -> SandboxResult`

Execute a script in the sandbox.

```python
result = sandbox.run_script("""
import os
print(os.getcwd())
""", language="python")
```

#### `copy_to_sandbox(local_path: str, container_path: str)`

Copy files into the sandbox.

```python
sandbox.copy_to_sandbox("./data.csv", "/workspace/data.csv")
```

#### `copy_from_sandbox(container_path: str, local_path: str)`

Copy files out of the sandbox.

```python
sandbox.copy_from_sandbox("/workspace/output.json", "./output.json")
```

### Functions

#### `is_docker_available() -> bool`

Check if Docker is available.

```python
from agentos.core.docker_sandbox import is_docker_available

if is_docker_available():
    sandbox = DockerSandbox()
else:
    print("Docker not available")
```

---

## Process Manager Module

`agentos.core.process_manager`

Real-time process monitoring and lifecycle management.

### Class: `ProcessMonitor` (Singleton)

```python
from agentos.core.process_manager import ProcessMonitor

monitor = ProcessMonitor()
```

### Methods

#### `register_agent(agent_id: str, pid: int, task: str = None)`

Register a new agent for monitoring.

```python
import os
monitor.register_agent("my_agent", os.getpid(), task="Data processing")
```

#### `unregister_agent(agent_id: str)`

Remove an agent from monitoring.

```python
monitor.unregister_agent("my_agent")
```

#### `get_running_agents() -> Dict[str, dict]`

Get all running agents with their status.

```python
agents = monitor.get_running_agents()
for agent_id, info in agents.items():
    print(f"{agent_id}: {info['status']}")
    print(f"  CPU: {info['cpu_percent']}%")
    print(f"  Memory: {info['memory_mb']} MB")
```

#### `get_agent_status(agent_id: str) -> dict`

Get status of a specific agent.

```python
status = monitor.get_agent_status("my_agent")
# Returns: {"status": "running", "cpu_percent": 5.2, "memory_mb": 128, ...}
```

#### `update_agent_status(agent_id: str, status: str)`

Update an agent's status.

```python
monitor.update_agent_status("my_agent", "completed")
```

### Context Manager: `AgentLifecycle`

```python
from agentos.core.process_manager import AgentLifecycle

with AgentLifecycle("my_agent", task="Process data") as lifecycle:
    # Agent automatically registered
    # CPU/memory monitored
    do_work()
# Automatically unregistered on exit
```

---

## Usage Examples

### Complete Security Flow

```python
from agentos.core.security import (
    validate_command, validate_input, sanitize_input,
    SecurityContext, ResourceLimits
)

limits = ResourceLimits(max_steps=10, timeout=60)

with SecurityContext(agent_id="secure_agent") as ctx:
    user_input = "list files; rm -rf /"

    # Validate input
    input_result = validate_input(user_input)
    if not input_result.is_safe:
        user_input = sanitize_input(user_input)

    # Validate command
    cmd_result = validate_command(user_input)
    if cmd_result.is_safe:
        # Execute safely
        pass
```

### Complete Agent Lifecycle

```python
from agentos.core.process_manager import AgentLifecycle
from agentos.core.shutdown import ShutdownContext
from agentos.core.retry import retry_with_backoff, DEFAULT_LLM_RETRY

@retry_with_backoff(DEFAULT_LLM_RETRY)
def call_llm(prompt):
    # API call with automatic retry
    return llm.complete(prompt)

with ShutdownContext():
    with AgentLifecycle("my_agent", task="Answer questions") as lifecycle:
        while not lifecycle.is_shutting_down():
            response = call_llm("Hello!")
            print(response)
```

---

## Error Handling

All modules raise descriptive exceptions:

```python
from agentos.core.security import SecurityError
from agentos.core.docker_sandbox import SandboxError
from agentos.core.chat_history import ChatHistoryError

try:
    sandbox.run_in_sandbox("command")
except SandboxError as e:
    print(f"Sandbox error: {e}")
```

---

## Configuration

Most modules respect settings in `default.yaml`:

```yaml
resource_limits:
  max_steps: 50
  timeout: 300
  max_memory_mb: 512

retry_config:
  max_retries: 3
  initial_delay: 1.0
  max_delay: 30.0

input_validation:
  enabled: true
  sanitize_by_default: true
```
