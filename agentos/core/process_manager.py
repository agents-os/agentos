"""Enhanced Process Management for AgentOS - Real-time Status Tracking"""

import logging
import os
import signal
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """
    Real-time process monitoring for running agents.
    Tracks status, logs, and provides lifecycle management.
    """

    _instance: Optional["ProcessMonitor"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._processes: Dict[str, Dict[str, Any]] = {}
        self._callbacks: List[Callable[[str, str, Dict], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._check_interval = 5.0  # seconds

        self._initialized = True

    def register_process(
        self,
        agent_id: str,
        name: str,
        pid: int,
        model: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Register a new process for monitoring."""
        with self._lock:
            self._processes[agent_id] = {
                "id": agent_id,
                "name": name,
                "pid": pid,
                "model": model,
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "last_check": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
            }
            logger.info(f"Registered process: {name} (PID {pid})")

        self._notify("registered", agent_id, self._processes[agent_id])

        # Start monitor if not running
        self._ensure_monitor_running()

    def unregister_process(self, agent_id: str, status: str = "stopped"):
        """Unregister a process from monitoring."""
        with self._lock:
            if agent_id in self._processes:
                process = self._processes.pop(agent_id)
                process["status"] = status
                process["stopped_at"] = datetime.now(timezone.utc).isoformat()
                logger.info(f"Unregistered process: {process['name']}")
                self._notify("unregistered", agent_id, process)

    def update_status(self, agent_id: str, status: str):
        """Update process status."""
        with self._lock:
            if agent_id in self._processes:
                self._processes[agent_id]["status"] = status
                self._processes[agent_id]["last_check"] = datetime.now(
                    timezone.utc
                ).isoformat()
                self._notify("status_changed", agent_id, self._processes[agent_id])

    def get_process(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get process info by ID."""
        with self._lock:
            return self._processes.get(agent_id, {}).copy()

    def get_all_processes(self) -> List[Dict[str, Any]]:
        """Get all monitored processes."""
        with self._lock:
            return [p.copy() for p in self._processes.values()]

    def get_running_count(self) -> int:
        """Get count of running processes."""
        with self._lock:
            return sum(1 for p in self._processes.values() if p["status"] == "running")

    def on_status_change(self, callback: Callable[[str, str, Dict], None]):
        """Register a callback for status changes."""
        self._callbacks.append(callback)

    def _notify(self, event: str, agent_id: str, data: Dict):
        """Notify all callbacks of an event."""
        for callback in self._callbacks:
            try:
                callback(event, agent_id, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def _ensure_monitor_running(self):
        """Ensure the monitor thread is running."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._running = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="process-monitor",
                daemon=True,
            )
            self._monitor_thread.start()

    def _monitor_loop(self):
        """Background thread that monitors process status."""
        while self._running:
            try:
                self._check_processes()
            except Exception as e:
                logger.error(f"Monitor error: {e}")

            time.sleep(self._check_interval)

    def _check_processes(self):
        """Check status of all monitored processes."""
        with self._lock:
            agent_ids = list(self._processes.keys())

        for agent_id in agent_ids:
            with self._lock:
                process = self._processes.get(agent_id)
                if not process:
                    continue

                pid = process["pid"]
                current_status = process["status"]

            # Skip if already in terminal state
            if current_status in ["stopped", "completed", "failed"]:
                continue

            # Check if process is still running
            is_running = self._is_process_running(pid)

            if not is_running and current_status == "running":
                # Process terminated
                self.update_status(agent_id, "stopped")
                logger.info(f"Process {process['name']} (PID {pid}) terminated")

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running."""
        if not pid:
            return False

        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def stop_monitor(self):
        """Stop the monitor thread."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)


class AgentLifecycle:
    """
    Manages the lifecycle of an agent process.
    Provides context manager support for clean startup/shutdown.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        model: str = "",
        auto_register: bool = True,
    ):
        self.agent_id = agent_id
        self.name = name
        self.model = model
        self.pid = os.getpid()
        self.auto_register = auto_register
        self._started = False
        self._monitor = get_process_monitor()

    def start(self):
        """Start the agent lifecycle."""
        if self._started:
            return

        if self.auto_register:
            self._monitor.register_process(
                agent_id=self.agent_id,
                name=self.name,
                pid=self.pid,
                model=self.model,
            )

            # Also register in database
            try:
                from agentos.database.db_agents import add_agent

                add_agent(self.agent_id, self.name, self.model, self.pid)
            except Exception as e:
                logger.warning(f"Could not register agent in database: {e}")

        self._started = True
        logger.info(f"Agent lifecycle started: {self.name}")

    def stop(self, status: str = "stopped"):
        """Stop the agent lifecycle."""
        if not self._started:
            return

        if self.auto_register:
            self._monitor.unregister_process(self.agent_id, status)

            # Also update database
            try:
                from agentos.database.db_agents import update_status

                update_status(self.agent_id, status)
            except Exception as e:
                logger.warning(f"Could not update agent status in database: {e}")

        self._started = False
        logger.info(f"Agent lifecycle stopped: {self.name} ({status})")

    def complete(self):
        """Mark the agent as completed."""
        self.stop("completed")

    def fail(self, error: Optional[str] = None):
        """Mark the agent as failed."""
        if error:
            logger.error(f"Agent {self.name} failed: {error}")
        self.stop("failed")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.fail(str(exc_val))
        elif self._started:
            self.complete()
        return False


# Global instance
_process_monitor: Optional[ProcessMonitor] = None


def get_process_monitor() -> ProcessMonitor:
    """Get the global process monitor instance."""
    global _process_monitor
    if _process_monitor is None:
        _process_monitor = ProcessMonitor()
    return _process_monitor


def get_running_agents() -> List[Dict[str, Any]]:
    """Get list of all running agents."""
    return get_process_monitor().get_all_processes()


def get_agent_status(agent_id: str) -> Optional[str]:
    """Get status of a specific agent."""
    process = get_process_monitor().get_process(agent_id)
    return process.get("status") if process else None
