"""
AgentOS - Production-Ready AI Agent Framework

A way to automate everything, even automation.

Features:
- Universal LLM Support (6+ providers: OpenAI, Claude, Gemini, Cohere, GitHub Models, Ollama)
- Interactive Chat Interface with Rich terminal UI
- Security-First Design (command filtering, input validation, Docker isolation)
- Process Management with SQLite-backed agent registry
- Simple YAML Manifests for configuration
- Retry Logic with exponential backoff
- Chat History with context preservation
- Graceful Shutdown support
- Extensible via MCP (Model Context Protocol)

Installation:
    pip install agentos-ai              # Basic installation
    pip install agentos-ai[full]        # Full installation with all features
    pip install agentos-ai[openai]      # With OpenAI support
    pip install agentos-ai[ollama]      # With Ollama (local models)

MIT Licensed - Free to use and modify.
"""

__version__ = "1.1.0"
__author__ = "AgentOS Team"
__license__ = "MIT"
__email__ = "support@agentos.dev"

# Core utilities
# Chat history persistence
from agentos.core.chat_history import (
    ChatHistoryManager,
    get_chat_history_manager,
)

# Configuration
from agentos.core.config import yaml_to_json

# Retry logic
from agentos.core.retry import (
    DEFAULT_LLM_RETRY,
    RetryConfig,
    retry_with_backoff,
)

# Security
from agentos.core.security import (
    ResourceLimits,
    SecurityContext,
    sanitize_input,
    validate_command,
    validate_input,
)

# Graceful shutdown
from agentos.core.shutdown import (
    ShutdownContext,
    get_shutdown_manager,
    graceful_shutdown,
    register_shutdown_callback,
)
from agentos.core.utils import (
    DESTRUCTIVE_COMMANDS,
    ISOLATED,
    MODEL,
    NAME,
    PROVIDER,
    SYSTEM_PROMPT,
    chat_history,
)

# Docker sandbox (optional)
try:
    from agentos.core.docker_sandbox import (
        DockerSandbox,
        is_docker_available,
        run_in_sandbox,
    )
except ImportError:
    DockerSandbox = None
    is_docker_available = lambda: False
    run_in_sandbox = None

# Process management
from agentos.core.process_manager import (
    AgentLifecycle,
    ProcessMonitor,
    get_process_monitor,
    get_running_agents,
)

# Agent execution (optional - depends on other modules)
try:
    from agentos.agent.agent_executor import (
        execute_command,
        execute_safe,
    )
except ImportError:
    execute_command = None
    execute_safe = None

# LLM providers (optional - may not have all dependencies)
try:
    from agentos.llm import (
        DEFAULT_MODELS,
        PROVIDERS,
        get_default_model,
        get_provider,
    )
except ImportError:
    PROVIDERS = {}
    DEFAULT_MODELS = {}
    get_provider = None
    get_default_model = None

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core
    "chat_history",
    "PROVIDER",
    "MODEL",
    "NAME",
    "ISOLATED",
    "DESTRUCTIVE_COMMANDS",
    "SYSTEM_PROMPT",
    "yaml_to_json",
    # Security
    "validate_command",
    "validate_input",
    "sanitize_input",
    "SecurityContext",
    "ResourceLimits",
    # Retry
    "RetryConfig",
    "retry_with_backoff",
    "DEFAULT_LLM_RETRY",
    # Chat history
    "ChatHistoryManager",
    "get_chat_history_manager",
    # Shutdown
    "get_shutdown_manager",
    "register_shutdown_callback",
    "graceful_shutdown",
    "ShutdownContext",
    # Docker
    "DockerSandbox",
    "run_in_sandbox",
    "is_docker_available",
    # Process management
    "ProcessMonitor",
    "AgentLifecycle",
    "get_process_monitor",
    "get_running_agents",
    # LLM
    "PROVIDERS",
    "DEFAULT_MODELS",
    "get_provider",
    "get_default_model",
    # Execution
    "execute_command",
    "execute_safe",
]
