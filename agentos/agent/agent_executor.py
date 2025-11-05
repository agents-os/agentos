"""Agent Command Execution Module"""

import logging
import os
import subprocess
import time
from typing import Tuple

from agentos.core import utils
from agentos.core.utils import DESTRUCTIVE_COMMANDS

logger = logging.getLogger(__name__)


def execute_command(command: str, simulate: bool = False, timeout: int = 30) -> Tuple[int, str]:
    """Execute command with security checks and timeout"""
    
    if not command or not command.strip():
        return 1, "ERROR: Empty command"
    
    command = command.strip()
    
    # Security: Check for destructive commands
    cmd_parts = command.lower().split()
    if any(dangerous in cmd_parts for dangerous in DESTRUCTIVE_COMMANDS):
        logger.warning(f"Blocked destructive command: {command}")
        return 1, f"ERROR: Destructive command blocked: {command}"
    
    # Security: Prevent command injection
    dangerous_patterns = [';', '&&', '||']
    if any(pattern in command for pattern in dangerous_patterns):
        logger.warning(f"Blocked potentially unsafe command: {command}")
        return 1, f"ERROR: Unsafe command pattern detected: {command}"
    
    # Block command substitution
    if '`' in command or '$(' in command:
        logger.warning(f"Blocked command substitution: {command}")
        return 1, f"ERROR: Command substitution blocked: {command}"
    
    if timeout <= 0 or timeout > 300:
        timeout = 30
    
    if utils.ISOLATED:
        try:
            from isolate import run_in_agentos
            logger.info(f"Executing in container: {command}")
            output = run_in_agentos(command)
            return 0, output.strip()
        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            return 1, f"Container error: {e}"

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
    else:
        try:
            logger.info(f"Executing command: {command}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True,
                cwd=os.getcwd(),
                env=os.environ.copy()
            )
            
            try:
                output, _ = process.communicate(timeout=timeout)
                return process.returncode, output.strip() if output else ""
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                logger.error(f"Command timed out after {timeout}s: {command}")
                return 124, f"Command timed out after {timeout} seconds"
                
        except FileNotFoundError:
            logger.error(f"Command not found: {command}")
            return 127, f"Command not found: {command.split()[0]}"
        except PermissionError:
            logger.error(f"Permission denied: {command}")
            return 126, f"Permission denied"
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}")
            return 1, f"Execution error: {e}"
