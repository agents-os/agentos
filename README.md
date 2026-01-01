# AgentOS - Production AI Agent Runtime

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/agentos/agentos)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

AgentOS is a production-ready runtime for autonomous AI agents with built-in memory management, safe tool sandboxing, and multi-provider LLM support.

## 🎬 Demo

<video controls width="720">
  <source src="assets/basic-tests.webm" type="video/webm">
  Your browser does not support the video tag — you can download the video: [assets/basic-tests.webm](assets/basic-tests.webm)
</video>

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

- **Comprehensive logging** with structured output
- **Error handling** and retry logic
- **Process management** with graceful shutdown
- **Security controls** blocking destructive commands
- **Timeout protection** preventing runaway processes

### � Interactive Chat Mode

- **Real-time conversations** with AI using any LLM provider
- **Rich terminal UI** with markdown rendering and color coding
- **Chat history management** with context preservation
- **Customizable prompts** and temperature settings
- **Offline support** with local Ollama models
- **API-free options** using GitHub or Ollama

### �🔒 Security First

- **Command filtering** blocks dangerous operations
- **Input validation** prevents command injection
- **Docker isolation** (optional) for safe execution
- **Resource limits** and timeout controls

### 🤖 Multi-LLM Support

- **GitHub Models** (default)
- **OpenAI** GPT-4, GPT-3.5
- **Anthropic Claude** 3.5
- **Google Gemini** 2.0
- **Cohere** Command
- **Ollama** (local models)

### 📊 Process Management

- **Agent registry** with SQLite backend
- **Status tracking** (running, completed, failed, stopped)
- **Log aggregation** per agent
- **Graceful shutdown** with SIGTERM/SIGKILL

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

Blocks dangerous commands:

- File deletion: `rm`, `rmdir`
- System modification: `sudo`, `chown`
- Disk operations: `dd`, `mkfs`, `fdisk`
- Process control: `kill`, `killall`

### Input Validation

Prevents command injection:

- Shell metacharacters: `;`, `&&`, `||`, `|`
- Command substitution: `` ` ``, `$()`
- Variable expansion: `$VAR`

### Resource Limits

- **Timeout**: 30s per command (configurable)
- **Step limit**: 10 steps per task (configurable)
- **Retry logic**: 3 attempts for LLM calls

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

<!-- - **Purchase**: [https://junaidahmed65.gumroad.com/l/spfzuo](https://junaidahmed65.gumroad.com/l/spfzuo) -->
- **Repository**: [https://github.com/agents-os/agentos](https://github.com/agents-os/agentos)
- **Issues**: [GitHub Issues](https://github.com/agents-os/agentos/issues)

---

**AgentOS** - Making AI agents production-ready, secure, and scalable.
