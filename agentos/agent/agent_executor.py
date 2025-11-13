"""Safe Agent Command Execution with Python Script Handling"""

import logging
import os
import re
import subprocess
import time
from typing import Tuple

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


def execute_command(
    command: str, simulate: bool = False, timeout: int = 30
) -> Tuple[int, str]:
    """Execute CLI commands safely, using whitelisted commands and Python execution for scripts."""

    if not command or not command.strip():
        return 1, "ERROR: Empty command"

    command = command.strip()
    cmd_lower = command.lower()

    # --- Block destructive commands ---
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

    # --- Handle isolated execution ---
    if utils.ISOLATED:
        try:
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
            return 124, "Command timed out"

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
