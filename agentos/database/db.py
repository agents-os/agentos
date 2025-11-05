"""Database Interface for AgentOS - Main Entry Point"""

from agentos.database.db_core import init_db, get_lock, get_connection, DB_DIR, DB_PATH, LOGS_DIR
from agentos.database.db_agents import (
    add_agent,
    update_status,
    list_agents,
    remove_agent,
    prune_stopped,
    get_agent,
    ps,
    stop,
    prune,
    logs,
    append_log,
)
from agentos.database.db_scheduler import (
    add_scheduled_agent,
    list_scheduled_agents,
    remove_scheduled_agent,
    update_scheduled_next_run,
)

__all__ = [
    'init_db',
    'get_lock',
    'get_connection',
    'DB_DIR',
    'DB_PATH',
    'LOGS_DIR',
    'add_agent',
    'update_status',
    'list_agents',
    'remove_agent',
    'prune_stopped',
    'get_agent',
    'ps',
    'stop',
    'prune',
    'logs',
    'append_log',
    'add_scheduled_agent',
    'list_scheduled_agents',
    'remove_scheduled_agent',
    'update_scheduled_next_run',
]


if __name__ == "__main__":
    import uuid
    import os

    test_id = str(uuid.uuid4())
    add_agent(test_id, "demo_agent", "local", os.getpid())
    ps()
    append_log("demo_agent", "Agent started successfully.")
    append_log("demo_agent", "Running task...")
    logs("demo_agent")
    stop("demo_agent")
    prune()
    ps()
