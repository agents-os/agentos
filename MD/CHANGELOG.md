# Changelog

All notable changes to AgentOS will be documented in this file.

## [1.1.0] - 2025-01-XX

### Added

- 🔄 **Retry Logic Module** (`agentos/core/retry.py`)

  - Exponential backoff with configurable jitter
  - Multiple retry strategies (DEFAULT_LLM_RETRY, AGGRESSIVE_RETRY, GENTLE_RETRY)
  - Per-provider retry configuration
  - `retry_with_backoff` decorator for easy integration

- 🛡️ **Enhanced Security Module** (`agentos/core/security.py`)

  - Expanded command filtering (20+ blocked commands)
  - Input sanitization with injection pattern detection
  - Path traversal protection
  - `ResourceLimits` dataclass for per-agent constraints
  - `SecurityContext` context manager for audit logging
  - `ValidationResult` for structured validation responses

- 💾 **Chat History Persistence** (`agentos/core/chat_history.py`)

  - SQLite-backed conversation storage
  - Full CRUD operations for conversations and messages
  - Search functionality across chat history
  - Export to JSON, Markdown, and plain text formats
  - Context retrieval for maintaining conversation flow

- 🛑 **Graceful Shutdown Support** (`agentos/core/shutdown.py`)

  - Signal handlers for SIGTERM/SIGINT
  - `ShutdownManager` singleton for centralized shutdown
  - Callback registration for cleanup tasks
  - `ShutdownContext` context manager for protected execution

- 🐳 **Enhanced Docker Sandbox** (`agentos/core/docker_sandbox.py`)

  - Memory and CPU limits
  - Network isolation modes
  - Read-only filesystem option
  - Automatic container cleanup
  - `is_docker_available()` health check

- 📊 **Process Manager** (`agentos/core/process_manager.py`)
  - Real-time CPU/memory monitoring
  - `ProcessMonitor` singleton for agent tracking
  - `AgentLifecycle` context manager
  - Status tracking with timestamps

### Enhanced

- LLM providers now use retry logic with exponential backoff
- Updated all package exports in `__init__.py` files
- Enhanced `default.yaml` with resource_limits, input_validation, and retry_config
- Improved `secure-agent.yaml` example with full security configuration

### Fixed

- Import errors with optional dependencies (graceful degradation)
- Module organization and export consistency

## [1.0.0] - 2024-01-XX

### Added

- 🚀 Initial production release
- 🎨 Enhanced UX with Rich-based CLI interface
- 📊 Interactive progress indicators and status displays
- 🛡️ Comprehensive security controls and command filtering
- 🐳 Docker isolation support for safe execution
- 📝 Structured logging with per-agent log files
- 🔄 Multi-provider LLM support (GitHub, OpenAI, Claude, Gemini, Cohere, Ollama)
- 📋 Agent registry with SQLite backend
- ⚡ Process management with graceful shutdown
- 🎯 Interactive manifest creation (`agentos init`)
- 📊 Enhanced agent status display with colors and emojis
- 🔍 Improved log viewing with syntax highlighting
- ⚠️ Smart warnings for potentially destructive tasks
- 📦 Package distribution support with setup.py
- 🐳 Production-ready Docker containers
- 📚 Comprehensive documentation and examples

### Features

- **CLI Commands**: run, ps, logs, stop, prune, init
- **Security**: Command filtering, input validation, Docker isolation
- **UX**: Progress bars, colored output, interactive prompts
- **Monitoring**: Real-time status, log streaming, health checks
- **Deployment**: Docker, pip package, docker-compose

### Security

- Blocks 25+ dangerous commands by default
- Prevents command injection attacks
- Optional Docker sandboxing
- Resource limits and timeouts
- Non-root container execution

### Performance

- Async LLM calls with retry logic
- Efficient process management
- Optimized Docker builds
- Resource usage monitoring

## [0.1.0] - 2024-01-XX

### Added

- Basic MVP implementation
- Core agent execution engine
- Simple CLI interface
- Basic logging and error handling
