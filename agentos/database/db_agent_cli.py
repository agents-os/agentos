"""CLI Helper Functions for Agent Database Operations"""

import os
import signal
import time
from datetime import datetime, timezone

from agentos.database.db_core import _LOCK, _get_conn, LOGS_DIR
from agentos.database.db_agent_ops import get_agent, list_agents, update_status, prune_stopped


def ps():
    """List all agents with enhanced status display"""
    agents = list_agents()
    if not agents:
        print("No agents found.")
        return

    print(f"{'ID':12} {'NAME':20} {'MODEL':20} {'STATUS':12} {'PID':8} {'STARTED':20}")
    print("-" * 95)

    for a in agents:
        agent_id = a["id"][:8] if a["id"] else "N/A"
        name = (a["name"] or "unknown")[:20]
        model = (a["model"] or "unknown")[:20]
        status = (a["status"] or "unknown")[:12]
        pid = str(a["pid"] or "N/A")[:8]
        started = (a["started_at"] or "N/A")[:20]

        if status == "running":
            status_colored = f"\033[92m{status}\033[0m"
        elif status == "completed":
            status_colored = f"\033[94m{status}\033[0m"
        elif status == "failed":
            status_colored = f"\033[91m{status}\033[0m"
        else:
            status_colored = f"\033[93m{status}\033[0m"

        print(f"{agent_id:12} {name:20} {model:20} {status_colored:12} {pid:8} {started:20}")


def stop(agent_id_or_name):
    """Stop an agent by ID or name"""
    agent = get_agent(agent_id_or_name)
    if not agent:
        print(f"❌ Agent '{agent_id_or_name}' not found.")
        return False

    if agent["status"] in ["stopped", "completed", "failed"]:
        print(f"ℹ️ Agent '{agent['name']}' is already {agent['status']}.")
        return True

    pid = agent["pid"]
    if not pid:
        print(f"⚠️ No PID found for agent '{agent['name']}'.")
        update_status(agent["id"], "stopped")
        return True

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)

        try:
            os.kill(pid, 0)
            print(f"⚠️ Force killing agent '{agent['name']}' (PID {pid})...")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

        update_status(agent["id"], "stopped")
        print(f"🛑 Stopped agent '{agent['name']}' (PID {pid}).")
        return True

    except ProcessLookupError:
        update_status(agent["id"], "stopped")
        print(f"⚠️ Process {pid} was already stopped.")
        return True
    except PermissionError:
        print(f"❌ Permission denied stopping agent '{agent['name']}' (PID {pid}).")
        return False
    except Exception as e:
        print(f"❌ Error stopping agent '{agent['name']}': {e}")
        return False


def prune():
    """Prune (delete) all stopped agent records"""
    before = len(list_agents())
    prune_stopped()
    after = len(list_agents())
    print(f"🧹 Pruned {before - after} stopped agent(s).")


def logs(agent_id_or_name):
    """Show log path or contents for a given agent"""
    agent = get_agent(agent_id_or_name)
    if not agent:
        print(f"❌ Agent '{agent_id_or_name}' not found.")
        return

    log_path = agent.get("log_path")
    if not log_path or not os.path.exists(log_path):
        print(f"ℹ️ No log file found for '{agent['name']}'.")
        return

    print(f"--- Logs for {agent['name']} ---")
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        print(f.read())


def append_log(agent_id_or_name, message):
    """Append a log line for a given agent"""
    agent = get_agent(agent_id_or_name)
    if not agent:
        print(f"❌ Agent '{agent_id_or_name}' not found.")
        return

    log_path = agent.get("log_path")
    if not log_path:
        log_path = os.path.join(LOGS_DIR, f"{agent['name']}.log")
        with _LOCK:
            with _get_conn() as conn:
                conn.execute(
                    "UPDATE agents SET log_path = ? WHERE id = ?",
                    (log_path, agent["id"]),
                )
                conn.commit()

    timestamp = datetime.now(timezone.utc).strftime("[%Y-%m-%d %H:%M:%S UTC]")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")

    print(f"📝 Logged to {log_path}: {message}")
