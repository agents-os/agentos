"""Graceful Shutdown Support for AgentOS"""

import atexit
import logging
import os
import signal
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ShutdownManager:
    """
    Manages graceful shutdown of AgentOS components.
    Supports cleanup callbacks, timeout-based forced shutdown, and signal handling.
    """

    _instance: Optional["ShutdownManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for shutdown manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the shutdown manager."""
        if self._initialized:
            return

        self._callbacks: List[tuple] = []  # (callback, priority, name)
        self._shutdown_in_progress = False
        self._shutdown_complete = False
        self._shutdown_timeout = 30.0  # seconds
        self._running_agents: Set[str] = set()
        self._callback_lock = threading.Lock()

        # Register signal handlers
        self._register_signals()

        # Register atexit handler
        atexit.register(self._atexit_handler)

        self._initialized = True
        logger.debug("ShutdownManager initialized")

    def _register_signals(self):
        """Register signal handlers for graceful shutdown."""
        # Only register in main thread
        if threading.current_thread() is not threading.main_thread():
            return

        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            if hasattr(signal, "SIGHUP"):
                signal.signal(signal.SIGHUP, self._signal_handler)
            logger.debug("Signal handlers registered")
        except Exception as e:
            logger.warning(f"Could not register signal handlers: {e}")

    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals."""
        signal_name = (
            signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        )
        logger.info(f"Received signal {signal_name}, initiating graceful shutdown...")

        # Print a newline if interrupted by Ctrl+C
        if signum == signal.SIGINT:
            print()

        self.shutdown(reason=f"Signal {signal_name}")

    def _atexit_handler(self):
        """Handle atexit cleanup."""
        if not self._shutdown_complete:
            self.shutdown(reason="Process exit")

    def register_callback(
        self,
        callback: Callable[[], None],
        priority: int = 50,
        name: Optional[str] = None,
    ):
        """
        Register a callback to be called during shutdown.

        Args:
            callback: Function to call during shutdown
            priority: Lower numbers are called first (0-100)
            name: Optional name for logging
        """
        with self._callback_lock:
            cb_name = name or callback.__name__
            self._callbacks.append((callback, priority, cb_name))
            # Sort by priority
            self._callbacks.sort(key=lambda x: x[1])
            logger.debug(
                f"Registered shutdown callback: {cb_name} (priority {priority})"
            )

    def unregister_callback(self, callback: Callable[[], None]):
        """Remove a shutdown callback."""
        with self._callback_lock:
            self._callbacks = [c for c in self._callbacks if c[0] != callback]

    def register_agent(self, agent_id: str):
        """Register a running agent."""
        self._running_agents.add(agent_id)
        logger.debug(f"Registered agent: {agent_id}")

    def unregister_agent(self, agent_id: str):
        """Unregister a stopped agent."""
        self._running_agents.discard(agent_id)
        logger.debug(f"Unregistered agent: {agent_id}")

    def get_running_agents(self) -> Set[str]:
        """Get set of currently running agent IDs."""
        return self._running_agents.copy()

    def set_timeout(self, timeout: float):
        """Set shutdown timeout in seconds."""
        self._shutdown_timeout = timeout

    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._shutdown_in_progress

    def shutdown(
        self, reason: str = "Manual shutdown", timeout: Optional[float] = None
    ):
        """
        Initiate graceful shutdown.

        Args:
            reason: Reason for shutdown (for logging)
            timeout: Override default timeout
        """
        if self._shutdown_in_progress:
            logger.warning("Shutdown already in progress")
            return

        self._shutdown_in_progress = True
        timeout = timeout or self._shutdown_timeout

        logger.info(f"Starting graceful shutdown: {reason}")
        logger.info(f"Shutdown timeout: {timeout}s")

        start_time = time.time()

        # Stop running agents
        if self._running_agents:
            logger.info(f"Stopping {len(self._running_agents)} running agents...")
            self._stop_agents(timeout=timeout / 2)

        # Execute callbacks
        with self._callback_lock:
            callbacks = list(self._callbacks)

        for callback, priority, name in callbacks:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.warning(
                    f"Shutdown timeout reached, skipping remaining callbacks"
                )
                break

            remaining = timeout - elapsed
            logger.debug(f"Executing shutdown callback: {name}")

            try:
                self._run_with_timeout(callback, remaining, name)
            except Exception as e:
                logger.error(f"Error in shutdown callback {name}: {e}")

        self._shutdown_complete = True
        elapsed = time.time() - start_time
        logger.info(f"Graceful shutdown complete in {elapsed:.2f}s")

    def _stop_agents(self, timeout: float):
        """Stop all running agents."""
        try:
            from agentos.database.db_agents import update_status

            agents = list(self._running_agents)
            for agent_id in agents:
                try:
                    update_status(agent_id, "stopped")
                    logger.info(f"Stopped agent: {agent_id}")
                except Exception as e:
                    logger.error(f"Error stopping agent {agent_id}: {e}")

            self._running_agents.clear()
        except ImportError:
            logger.warning("Could not import db_agents module for agent cleanup")

    def _run_with_timeout(self, func: Callable, timeout: float, name: str):
        """Run a function with a timeout."""
        result = [None]
        error = [None]

        def wrapper():
            try:
                result[0] = func()
            except Exception as e:
                error[0] = e

        thread = threading.Thread(target=wrapper, name=f"shutdown-{name}")
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            logger.warning(f"Callback {name} did not complete within timeout")

        if error[0]:
            raise error[0]

        return result[0]


# Convenience functions


def get_shutdown_manager() -> ShutdownManager:
    """Get the singleton shutdown manager instance."""
    return ShutdownManager()


def register_shutdown_callback(
    callback: Callable[[], None],
    priority: int = 50,
    name: Optional[str] = None,
):
    """Register a shutdown callback."""
    get_shutdown_manager().register_callback(callback, priority, name)


def is_shutting_down() -> bool:
    """Check if shutdown is in progress."""
    return get_shutdown_manager().is_shutting_down()


def graceful_shutdown(reason: str = "Manual shutdown"):
    """Initiate graceful shutdown."""
    get_shutdown_manager().shutdown(reason)


class ShutdownContext:
    """Context manager for graceful shutdown support."""

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id
        self.manager = get_shutdown_manager()

    def __enter__(self):
        if self.agent_id:
            self.manager.register_agent(self.agent_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.agent_id:
            self.manager.unregister_agent(self.agent_id)
        return False

    def check_shutdown(self) -> bool:
        """Check if shutdown was requested. Returns True if should stop."""
        return self.manager.is_shutting_down()
