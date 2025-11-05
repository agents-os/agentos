"""Basic Agent Database Operations"""

import sqlite3
from datetime import datetime, timezone

from agentos.database.db_core import _LOCK, _get_conn


def add_agent(agent_id, name, model, pid, log_path=None):
    """Add a new running agent record"""
    if not agent_id or not name or not model:
        raise ValueError("agent_id, name, and model are required")
    
    with _LOCK:
        conn = None
        try:
            conn = _get_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO agents (id, name, model, pid, status, started_at, log_path)
                VALUES (?, ?, ?, ?, 'running', ?, ?)
            """,
                (
                    agent_id,
                    name,
                    model,
                    pid,
                    datetime.now(timezone.utc).isoformat(),
                    log_path or f"~/.agentos/logs/{name}_{agent_id[:8]}.log",
                ),
            )
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error adding agent: {e}")
        finally:
            if conn:
                conn.close()


def update_status(agent_id, status):
    """Update an agent's status"""
    valid_statuses = ['running', 'stopped', 'completed', 'failed']
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
    
    with _LOCK:
        conn = None
        try:
            conn = _get_conn()
            stopped_at = (
                datetime.now(timezone.utc).isoformat() if status in ['stopped', 'completed', 'failed'] else None
            )
            conn.execute(
                """
                UPDATE agents
                SET status = ?, stopped_at = ?
                WHERE id = ?
            """,
                (status, stopped_at, agent_id),
            )
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error updating status: {e}")
        finally:
            if conn:
                conn.close()


def list_agents(status=None):
    """Return a list of all agents"""
    with _LOCK:
        conn = None
        try:
            conn = _get_conn()
            if status:
                cur = conn.execute("SELECT * FROM agents WHERE status = ? ORDER BY started_at DESC", (status,))
            else:
                cur = conn.execute("SELECT * FROM agents ORDER BY started_at DESC")
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error listing agents: {e}")
        finally:
            if conn:
                conn.close()


def remove_agent(agent_id):
    """Remove an agent record by ID"""
    with _LOCK:
        conn = None
        try:
            conn = _get_conn()
            conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error removing agent: {e}")
        finally:
            if conn:
                conn.close()


def prune_stopped():
    """Remove all stopped, completed, and failed agent records"""
    with _LOCK:
        conn = None
        try:
            conn = _get_conn()
            conn.execute("DELETE FROM agents WHERE status IN ('stopped', 'completed', 'failed')")
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error pruning agents: {e}")
        finally:
            if conn:
                conn.close()


def get_agent(agent_id_or_name):
    """Fetch a single agent's info by ID or name"""
    with _LOCK:
        conn = None
        try:
            conn = _get_conn()
            cur = conn.execute(
                """
                SELECT * FROM agents WHERE id = ? OR id LIKE ? || '%' OR name = ?
                ORDER BY CASE WHEN id = ? THEN 0 WHEN id LIKE ? || '%' THEN 1 ELSE 2 END
                LIMIT 1
            """,
                (agent_id_or_name, agent_id_or_name, agent_id_or_name, agent_id_or_name, agent_id_or_name),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error getting agent: {e}")
        finally:
            if conn:
                conn.close()
