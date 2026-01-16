"""Safe Agent Command Execution with Python Script Handling and Security"""

import logging
import os
import re
import subprocess
import time
from typing import Optional, Tuple

from agentos.core import utils
from agentos.core.utils import DESTRUCTIVE_COMMANDS

logger = logging.getLogger(__name__)

# --- Safe command whitelist ---
SAFE_COMMANDS = (
    "echo",
    "cat",
    "python",
    "python3",
    "ls",
    "touch",
    "mkdir",
    "cp",
    "mv",
    "grep",
    "head",
    "tail",
    "pwd",
    "find",
    "chmod",
)

# Lazy imports for security module to avoid circular imports
_security_context = None


def _get_security_context():
    """Get security context with lazy import."""
    global _security_context
    if _security_context is None:
        try:
            from agentos.core.security import DEFAULT_LIMITS, SecurityContext

            _security_context = SecurityContext(
                blocked_commands=set(DESTRUCTIVE_COMMANDS),
                resource_limits=DEFAULT_LIMITS,
            )
        except ImportError:
            _security_context = None
    return _security_context


def _is_shutting_down() -> bool:
    """Check if shutdown is in progress (lazy import)."""
    try:
        from agentos.core.shutdown import is_shutting_down

        return is_shutting_down()
    except ImportError:
        return False


def _validate_command_security(command: str) -> Tuple[bool, str]:
    """Validate command using security module if available."""
    try:
        from agentos.core.security import validate_command

        result = validate_command(command, set(DESTRUCTIVE_COMMANDS))
        return result.is_valid, result.message
    except ImportError:
        # Fallback to basic validation
        return True, "OK"


def execute_command(
    command: str,
    simulate: bool = False,
    timeout: int = 30,
) -> Tuple[int, str]:
    """
    Execute CLI commands safely with multiple layers of protection.

    Security features:
    - Command filtering (blocks dangerous operations)
    - Input validation (prevents injection attacks)
    - Timeout enforcement (resource limits)
    - Graceful shutdown support
    - Optional Docker isolation

    Args:
        command: The command to execute
        simulate: If True, simulate output using LLM instead of executing
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (exit_code, output)
    """

    # Check for shutdown
    if _is_shutting_down():
        return 1, "ERROR: Shutdown in progress"

    if not command or not command.strip():
        return 1, "ERROR: Empty command"

    command = command.strip()
    cmd_lower = command.lower()

    # --- Enhanced security validation ---
    is_valid, security_msg = _validate_command_security(command)
    if not is_valid:
        logger.warning(f"Security validation failed: {security_msg}")
        return 1, f"ERROR: {security_msg}"

    # --- Block destructive commands (fallback check) ---
    cmd_parts = re.split(r"\s+", cmd_lower)
    if any(d in cmd_parts for d in DESTRUCTIVE_COMMANDS):
        logger.warning(f"Blocked destructive command: {command}")
        return 1, f"ERROR: Destructive command blocked: {command}"

    # --- Block unsafe command chaining ---
    if any(sym in command for sym in [";", "&&", "||", "|&"]):
        logger.warning(f"Blocked unsafe chained command: {command}")
        return 1, f"ERROR: Unsafe command chaining detected: {command}"

    # --- Block command substitution & untrusted expansions ---
    if any(sym in command for sym in ["`", "$("]):
        if not any(command.strip().startswith(safe) for safe in SAFE_COMMANDS):
            if re.search(r"`[^`]+`|\$\([^)]*\)", command):
                logger.warning(f"Blocked command substitution: {command}")
                return 1, f"ERROR: Command substitution blocked: {command}"

    # --- Normalize timeout ---
    if timeout <= 0 or timeout > 300:
        timeout = 30

    # --- Handle isolated execution (Docker sandbox) ---
    if utils.ISOLATED:
        try:
            # Try enhanced Docker sandbox first
            try:
                from agentos.core.docker_sandbox import (
                    is_docker_available,
                    run_in_sandbox,
                )

                if is_docker_available():
                    logger.info(f"Executing in Docker sandbox: {command}")
                    exit_code, output = run_in_sandbox(command, timeout=timeout)
                    return exit_code, output.strip()
            except ImportError:
                pass

            # Fallback to legacy isolate module
            from agentos.core.isolate import run_in_agentos

            logger.info(f"Executing in isolated mode: {command}")
            output = run_in_agentos(command)
            return 0, output.strip()
        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            return 1, f"Container error: {e}"

    # --- Simulation mode ---
    if simulate:
        try:
            time.sleep(0.5)
            from agentos.agent.agent_planner import ask_llm

            output = ask_llm(
                "You are simulating CLI output.",
                f"Simulate realistic output for this command: {command}",
            )
            return 0, output.strip()
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            return 1, f"Simulation error: {e}"

    # --- Actual command execution ---
    try:
        # If the command is a Python script, run it explicitly via python3
        if command.endswith(".py"):
            command = f"/usr/bin/python3 {command}"

        logger.info(f"Executing command: {command}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy(),
        )

        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
            logger.error(f"Command timed out after {timeout}s: {command}")
            return 124, f"Command timed out after {timeout}s"

        return process.returncode, output.strip() if output else ""

    except FileNotFoundError:
        logger.error(f"Command not found: {command}")
        return 127, f"Command not found: {command.split()[0]}"
    except PermissionError:
        logger.error(f"Permission denied: {command}")
        return 126, "Permission denied"
    except Exception as e:
        logger.error(f"Unexpected error executing command: {e}")
        return 1, f"Execution error: {e}"


def execute_safe(
    command: str,
    timeout: int = 30,
    allow_chaining: bool = False,
) -> Tuple[int, str]:
    """
    Execute a command with strict safety checks.

    This is a stricter version of execute_command that:
    - Never allows command chaining unless explicitly enabled
    - Always validates against injection attacks
    - Has stricter timeout limits

    Args:
        command: The command to execute
        timeout: Maximum execution time (capped at 60s)
        allow_chaining: Allow && and || operators

    Returns:
        Tuple of (exit_code, output)
    """
    # Cap timeout
    timeout = min(timeout, 60)

    # Check for chaining
    if not allow_chaining:
        if any(sym in command for sym in [";", "&&", "||", "|", "`", "$(", "${"]):
            return 1, "ERROR: Command chaining/substitution not allowed in safe mode"

    return execute_command(command, simulate=False, timeout=timeout)
