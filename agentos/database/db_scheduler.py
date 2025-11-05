"""Scheduler Database Operations"""

from datetime import datetime, timezone

from agentos.database.db_core import _LOCK, _get_conn


def add_scheduled_agent(schedule_id, name, manifest_path, task, schedule_type, time_config=None, repeat_config=None, next_run=None):
    """Add a scheduled agent to the database"""
    with _LOCK:
        with _get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scheduled_agents 
                (id, name, manifest_path, task, schedule_type, time_config, repeat_config, next_run, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    schedule_id,
                    name,
                    manifest_path,
                    task,
                    schedule_type,
                    time_config,
                    repeat_config,
                    next_run,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()


def list_scheduled_agents():
    """Return a list of all scheduled agents"""
    with _LOCK:
        with _get_conn() as conn:
            cur = conn.execute("SELECT * FROM scheduled_agents")
            return [dict(row) for row in cur.fetchall()]


def remove_scheduled_agent(schedule_id):
    """Remove a scheduled agent by ID"""
    with _LOCK:
        with _get_conn() as conn:
            conn.execute("DELETE FROM scheduled_agents WHERE id = ?", (schedule_id,))
            conn.commit()


def update_scheduled_next_run(schedule_id, next_run):
    """Update the next run time for a scheduled agent"""
    with _LOCK:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE scheduled_agents SET next_run = ? WHERE id = ?",
                (next_run, schedule_id)
            )
            conn.commit()
