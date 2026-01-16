"""AgentOS Core Module - Production-Ready Components"""

# Chat history persistence
from agentos.core.chat_history import (
    ChatHistoryManager,
    get_chat_history_manager,
)
from agentos.core.config import yaml_to_json

# Docker sandbox
from agentos.core.docker_sandbox import (
    DockerSandbox,
    get_sandbox,
    is_docker_available,
    run_in_sandbox,
)

# Process management
from agentos.core.process_manager import (
    AgentLifecycle,
    ProcessMonitor,
    get_agent_status,
    get_process_monitor,
    get_running_agents,
)

# Retry logic
from agentos.core.retry import (
    AGGRESSIVE_RETRY,
    DEFAULT_LLM_RETRY,
    GENTLE_RETRY,
    LLM_API_RETRY,
    RetryConfig,
    retry_with_backoff,
)

# Security
from agentos.core.security import (
    BLOCKED_COMMANDS,
    DEFAULT_LIMITS,
    RELAXED_LIMITS,
    STRICT_LIMITS,
    ResourceLimits,
    SecurityContext,
    ValidationResult,
    sanitize_filename,
    sanitize_input,
    sanitize_path,
    validate_command,
    validate_input,
)

# Graceful shutdown
from agentos.core.shutdown import (
    ShutdownContext,
    ShutdownManager,
    get_shutdown_manager,
    graceful_shutdown,
    is_shutting_down,
    register_shutdown_callback,
)
from agentos.core.utils import (
    DESTRUCTIVE_COMMANDS,
    ISOLATED,
    MCP_ENABLED,
    MCP_SERVERS,
    MODEL,
    NAME,
    PERMS,
    PROVIDER,
    REPEAT_CONFIG,
    SYSTEM_PROMPT,
    TIME_CONFIG,
    chat_history,
)

__all__ = [
    # Config
    "yaml_to_json",
    # Utils
    "chat_history",
    "PERMS",
    "PROVIDER",
    "MODEL",
    "NAME",
    "ISOLATED",
    "TIME_CONFIG",
    "REPEAT_CONFIG",
    "MCP_ENABLED",
    "MCP_SERVERS",
    "DESTRUCTIVE_COMMANDS",
    "SYSTEM_PROMPT",
    # Retry
    "RetryConfig",
    "retry_with_backoff",
    "DEFAULT_LLM_RETRY",
    "AGGRESSIVE_RETRY",
    "GENTLE_RETRY",
    "LLM_API_RETRY",
    # Security
    "validate_command",
    "validate_input",
    "sanitize_input",
    "sanitize_path",
    "sanitize_filename",
    "ValidationResult",
    "ResourceLimits",
    "SecurityContext",
    "BLOCKED_COMMANDS",
    "DEFAULT_LIMITS",
    "STRICT_LIMITS",
    "RELAXED_LIMITS",
    # Chat history
    "ChatHistoryManager",
    "get_chat_history_manager",
    # Shutdown
    "ShutdownManager",
    "get_shutdown_manager",
    "register_shutdown_callback",
    "is_shutting_down",
    "graceful_shutdown",
    "ShutdownContext",
    # Docker
    "DockerSandbox",
    "get_sandbox",
    "run_in_sandbox",
    "is_docker_available",
    # Process management
    "ProcessMonitor",
    "AgentLifecycle",
    "get_process_monitor",
    "get_running_agents",
    "get_agent_status",
]
