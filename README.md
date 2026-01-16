# AgentOS - Production AI Agent Runtime

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/agentos/agentos)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

AgentOS is a production-ready runtime for autonomous AI agents with built-in memory management, safe tool sandboxing, and multi-provider LLM support.

## 🎬 Demo

![Preview](./assets/basic-chat.gif)

## 🚀 Quick Start

### Installation

<!-- Purchase and download from: **https://junaidahmed65.gumroad.com/l/spfzuo**  -->

Then run the installer:

```bash
# Linux
python3 install_linux.py

# Windows
python install_windows.py
```

### Basic Usage

1. Create an agent manifest (`agent.yaml`):

```yaml
name: my_assistant
model_provider: github
model_version: openai/gpt-4o-mini
isolated: false
```

2. Run your agent:

```bash
agentos run agent.yaml --task "create a Python script that prints hello world"
```

3. Monitor running agents:

```bash
agentos ps
```

## 🏗️ Features

### ✅ Production Ready

- **Comprehensive logging** with structured output and per-agent log files
- **Intelligent retry logic** with exponential backoff for LLM API calls
- **Process management** with real-time monitoring and graceful shutdown
- **Security controls** blocking destructive commands and injection attacks
- **Timeout protection** preventing runaway processes
- **Resource limits** for memory, CPU, and execution steps

### 💬 Interactive Chat Mode

- **Real-time conversations** with AI using any LLM provider
- **Rich terminal UI** with markdown rendering and syntax highlighting
- **Persistent chat history** with SQLite backend and search functionality
- **Conversation export** to JSON, Markdown, or plain text formats
- **Context preservation** across sessions with configurable context window
- **Customizable prompts** and temperature settings
- **Offline support** with local Ollama models
- **API-free options** using GitHub or Ollama

### 🔒 Security First

- **Command filtering** blocks 20+ dangerous operations (rm, sudo, dd, etc.)
- **Input validation** prevents shell injection with pattern detection
- **Path traversal protection** blocks `../` and absolute path escapes
- **Docker isolation** (optional) with memory/CPU limits and network isolation
- **Resource limits** configurable per-agent (memory, CPU, timeout, steps)
- **Security context** for audit logging and tracking

### 🤖 Multi-LLM Support (6+ Providers)

- **GitHub Models** (default) - Free tier available
- **OpenAI** GPT-4o, GPT-4, GPT-3.5-turbo
- **Anthropic Claude** 3.5 Sonnet, Claude 3 Opus
- **Google Gemini** 2.0 Flash, 1.5 Pro
- **Cohere** Command R+, Command
- **Ollama** (local models) - No API key required

### 📊 Process Management

- **Agent registry** with SQLite backend
- **Real-time process monitoring** with CPU/memory tracking
- **Status tracking** (running, completed, failed, stopped)
- **Log aggregation** per agent with rotation support
- **Graceful shutdown** with signal handlers (SIGTERM/SIGINT)
- **Agent lifecycle management** with context managers

### 🔄 Retry Logic & Resilience

- **Exponential backoff** with configurable jitter
- **Automatic retry** for transient API failures
- **Customizable retry strategies** (aggressive, gentle, default)
- **Per-provider retry configuration**
- **Circuit breaker patterns** for failing services

## 📋 Commands

### Run Agent

```bash
agentos run <manifest> --task "<task>" [--timeout 300] [--verbose]
```

### Interactive Chat Mode ✨

Chat with any LLM provider in a conversational interface:

```bash
# Start chat with default OpenAI
agentos chat

# Use different providers
agentos chat --provider claude
agentos chat --provider gemini --temperature 0.3
agentos chat --provider ollama  # Local models, no API key needed

# Customize the experience
agentos chat --system-prompt "You are a Python expert"
agentos chat --provider openai --model gpt-4
```

**In-chat commands:** `exit` / `quit` (end), `clear` (history), `help` (commands), `status` (info)

See [Chat Mode Guide](MD/CHAT_MODE.md) for detailed usage.

### List Agents

```bash
agentos ps
```

### View Logs

```bash
agentos logs <agent_name> [--tail 50]
```

### Stop Agent

```bash
agentos stop <agent_name>
```

### Clean Up

```bash
agentos prune  # Remove stopped agents
```

## 📝 Agent Manifest

```yaml
name: research_assistant
model_provider: github
model_version: openai/gpt-4o-mini
isolated: false

DESTRUCTIVE_COMMANDS:
  - rm
  - rmdir
  - sudo
  - dd
  - mkfs
  - format
```

### Required Fields

- `name`: Agent identifier
- `model_provider`: LLM provider (github, openai, claude, gemini, cohere, ollama)
- `model_version`: Specific model to use

### Optional Fields

- `isolated`: Enable Docker sandboxing (default: true)
- `DESTRUCTIVE_COMMANDS`: Custom list of blocked commands

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# API Keys (set as needed)
GIT_HUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_key
CLAUDE_API_KEY=your_claude_key
GEMINI_API_KEY=your_gemini_key
COHERE_API_KEY=your_cohere_key
```

### Logging

Logs are stored in `~/.agentos/logs/`:

- `agentos.log` - Main system log
- `<agent_name>_<id>.log` - Per-agent execution logs

### Database

Agent registry stored in `~/.agentos/runtime.db` (SQLite)

## 🧰 MCP Tooling (Optional)

AgentOS can prefer MCP servers (Model Context Protocol) instead of emitting shell commands.

- Enable MCP in your manifest:

```yaml
mcp:
  enabled: true
  servers:
    - name: local_tools
      kind: stdio
      command: my-mcp-server --stdio
```

- Install a Python MCP SDK (one of):

```bash
pip install mcp
# or install the official Model Context Protocol Python SDK if available
```

- Chat/Web will now prompt models to output MCP calls in a JSON block. AgentOS parses and executes those calls via the MCP client, with safe fallback to command extraction when no MCP calls are present.

## 🐳 Docker Support

Enable isolation for safe execution:

```yaml
name: secure_agent
model_provider: github
model_version: openai/gpt-4o-mini
isolated: true
```

Requires Docker daemon running.

## 🛡️ Security Features

### Command Filtering

Blocks dangerous commands automatically:

- File deletion: `rm`, `rmdir`, `shred`
- System modification: `sudo`, `su`, `chown`, `chmod`
- Disk operations: `dd`, `mkfs`, `fdisk`, `format`
- Process control: `kill`, `killall`, `pkill`
- Network: `nc`, `netcat`, `wget`, `curl` (to unknown hosts)

### Input Validation

Prevents command injection attacks:

- Shell metacharacters: `;`, `&&`, `||`, `|`
- Command substitution: `` ` ``, `$()`
- Variable expansion: `$VAR`, `${VAR}`
- Path traversal: `../`, absolute paths outside workspace

### Resource Limits

Configure per-agent resource constraints:

```yaml
resource_limits:
  max_steps: 50 # Maximum execution steps
  timeout: 300 # Timeout in seconds
  max_memory_mb: 512 # Memory limit (Docker only)
  max_cpu_percent: 50 # CPU limit (Docker only)
```

### Security Context

Track and audit agent actions:

```python
from agentos.core.security import SecurityContext, validate_command

with SecurityContext(agent_id="my_agent") as ctx:
    result = validate_command("ls -la")
    if result.is_safe:
        # Execute command
        pass
    # All actions logged automatically
```

## 🔄 Retry Configuration

Configure retry behavior for LLM API calls:

```yaml
retry_config:
  max_retries: 3 # Maximum retry attempts
  initial_delay: 1.0 # Initial delay in seconds
  max_delay: 30.0 # Maximum delay cap
  exponential_base: 2.0 # Exponential backoff multiplier
  jitter: true # Add randomness to prevent thundering herd
```

### Retry Strategies

```python
from agentos.core.retry import DEFAULT_LLM_RETRY, AGGRESSIVE_RETRY, GENTLE_RETRY

# Default: 3 retries, 1-30s delay
config = DEFAULT_LLM_RETRY

# Aggressive: 5 retries, 0.5-60s delay (for critical operations)
config = AGGRESSIVE_RETRY

# Gentle: 2 retries, 2-10s delay (for user-facing features)
config = GENTLE_RETRY
```

## 💾 Chat History

Persistent chat history with SQLite backend:

```python
from agentos.core.chat_history import ChatHistoryManager

# Initialize manager
history = ChatHistoryManager()

# Create conversation
conv_id = history.create_conversation(
    agent_id="assistant",
    title="Python Help Session"
)

# Add messages
history.add_message(conv_id, "user", "How do I read a file?")
history.add_message(conv_id, "assistant", "Use open() function...")

# Search history
results = history.search_messages("file", agent_id="assistant")

# Export conversation
history.export_conversation(conv_id, "chat.md", format="markdown")
```

## 🐳 Docker Sandbox

Enhanced Docker isolation for safe execution:

```yaml
name: secure_agent
model_provider: github
model_version: openai/gpt-4o-mini
isolated: true
```

### Advanced Docker Configuration

```python
from agentos.core.docker_sandbox import DockerSandbox

sandbox = DockerSandbox(
    memory_limit="256m",      # Memory constraint
    cpu_quota=50000,          # CPU microseconds per period
    network_mode="none",      # No network access
    read_only=True,           # Read-only filesystem
    working_dir="/workspace"
)

result = sandbox.run_in_sandbox("python script.py")
```

Requires Docker daemon running.

## 📊 Process Monitoring

Real-time process monitoring and lifecycle management:

```python
from agentos.core.process_manager import ProcessMonitor, AgentLifecycle

# Get singleton monitor
monitor = ProcessMonitor()

# Use lifecycle context manager
with AgentLifecycle("my_agent", task="Process data") as agent:
    # Agent is registered and tracked
    # CPU/memory monitored in real-time
    pass  # Do work
# Automatically cleaned up

# Query running agents
agents = monitor.get_running_agents()
for agent_id, info in agents.items():
    print(f"{agent_id}: {info['status']} - CPU: {info['cpu_percent']}%")
```

## 🛑 Graceful Shutdown

Signal handling for clean termination:

```python
from agentos.core.shutdown import ShutdownManager, ShutdownContext

# Register cleanup callbacks
manager = ShutdownManager()
manager.register_callback(lambda: print("Cleaning up..."))

# Use context manager
with ShutdownContext():
    # Protected execution
    # SIGTERM/SIGINT handled gracefully
    pass
```

## 📊 Monitoring

### Status Codes

- `running`: Agent is executing
- `completed`: Task finished successfully
- `failed`: Task failed with error
- `stopped`: Manually terminated

### Exit Codes

- `0`: Success
- `1`: General error
- `124`: Timeout
- `130`: User interrupt (Ctrl+C)

## 🧩 Architecture

```
agentos/
├── agent/          # Agent execution and planning
├── cli/            # Command-line interface
├── core/           # Core utilities
│   ├── config.py       # Configuration management
│   ├── retry.py        # Retry logic with backoff
│   ├── security.py     # Security validation
│   ├── chat_history.py # Persistent chat storage
│   ├── shutdown.py     # Graceful shutdown
│   ├── docker_sandbox.py # Docker isolation
│   └── process_manager.py # Process monitoring
├── database/       # SQLite backend
├── llm/            # LLM provider integrations
├── mcp/            # Model Context Protocol
└── web/            # Web UI
```

## 🔄 Development

### Local Setup

```bash
git clone https://github.com/agents-os/agentos
cd agentos
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Testing

```bash
python -m pytest tests/
```

### Code Quality

```bash
black .
flake8 .
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Repository**: [https://github.com/agents-os/agentos](https://github.com/agents-os/agentos)
- **Issues**: [GitHub Issues](https://github.com/agents-os/agentos/issues)

---

**AgentOS** - Making AI agents production-ready, secure, and scalable.
