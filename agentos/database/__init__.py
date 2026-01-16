"""AgentOS Database Module - SQLite-backed Agent Registry and Process Management"""

from agentos.database.db_agents import (
    add_agent,
    append_log,
    get_agent,
    list_agents,
    logs,
    prune,
    prune_stopped,
    ps,
    remove_agent,
    stop,
    update_status,
)
from agentos.database.db_core import (
    _LOCK,
    _get_conn,
)

__all__ = [
    # Agent CRUD operations
    "add_agent",
    "update_status",
    "list_agents",
    "remove_agent",
    "prune_stopped",
    "get_agent",
    # CLI helpers
    "ps",
    "stop",
    "prune",
    "logs",
    "append_log",
    # Core DB
    "_get_conn",
    "_LOCK",
]
