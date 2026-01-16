"""Security-First Design for AgentOS - Input Validation & Command Filtering"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# DANGEROUS COMMAND PATTERNS
# =============================================================================

# Commands that are absolutely blocked
BLOCKED_COMMANDS: Set[str] = {
    # File destruction
    "rm",
    "rmdir",
    "del",
    "erase",
    "rd",
    "shred",
    "wipe",
    # Disk operations
    "dd",
    "mkfs",
    "fdisk",
    "format",
    "parted",
    "mkswap",
    # Privilege escalation
    "sudo",
    "su",
    "doas",
    "pkexec",
    "runas",
    # System control
    "reboot",
    "shutdown",
    "halt",
    "poweroff",
    "init",
    # Process control (dangerous)
    "kill",
    "killall",
    "pkill",
    "xkill",
    # Dangerous file operations
    "truncate",
    "chown",
    "chmod",
    # Cron and systemd
    "crontab",
    "systemctl",
    "service",
    # Mount operations
    "mount",
    "umount",
    "fusermount",
    # Network attacks
    "nc",
    "netcat",
    "nmap",
    "hping",
}

# Patterns that indicate dangerous command structures
DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    # Fork bomb patterns
    (r":\(\)\s*{\s*:\|:&\s*}", "fork bomb detected"),
    (r"\$\(.*:\(\)", "fork bomb variant detected"),
    # Recursive deletion
    (r"rm\s+(-[rf]+\s+)+/", "recursive deletion of root"),
    (r"rm\s+(-[rf]+\s+)+~", "recursive deletion of home"),
    (r"rm\s+(-[rf]+\s+)+\*", "recursive deletion with wildcard"),
    # Dangerous redirects
    (r">\s*/dev/sd[a-z]", "direct write to block device"),
    (r">\s*/dev/null.*<", "null device abuse"),
    # DD dangerous operations
    (r"dd\s+.*of=/dev/", "dd write to device"),
    (r"dd\s+.*if=/dev/zero", "dd from zero device"),
    (r"dd\s+.*if=/dev/random", "dd from random device"),
    # Privilege escalation attempts
    (r"sudo\s+-S", "sudo with password from stdin"),
    (r"echo.*\|\s*sudo", "piped sudo attempt"),
    # Encoded payloads
    (r"base64\s+-d.*\|\s*(?:bash|sh|python)", "encoded payload execution"),
    (r"echo\s+[A-Za-z0-9+/=]+\s*\|\s*base64", "base64 encoded command"),
    # Curl/wget to shell
    (r"curl.*\|\s*(?:bash|sh)", "remote code execution via curl"),
    (r"wget.*\|\s*(?:bash|sh)", "remote code execution via wget"),
    (r"curl.*-o-.*\|\s*(?:bash|sh)", "curl piped to shell"),
]


# =============================================================================
# INJECTION ATTACK PATTERNS
# =============================================================================

# Characters/sequences that could enable command injection
INJECTION_PATTERNS: List[Tuple[str, str]] = [
    # Command chaining
    (r";\s*\w", "semicolon command chaining"),
    (r"&&", "AND command chaining"),
    (r"\|\|", "OR command chaining"),
    (r"\|&", "pipe with stderr"),
    # Command substitution
    (r"`[^`]+`", "backtick command substitution"),
    (r"\$\([^)]+\)", "dollar-paren command substitution"),
    # Variable expansion attacks
    (r"\$\{[^}]*[;|&]", "malicious variable expansion"),
    (r"\$\{.*:-.*[;|&]", "default value injection"),
    # Newline injection
    (r"\\n\s*\w", "newline injection"),
    (r"\x0a", "raw newline byte"),
    (r"\x0d", "raw carriage return byte"),
    # Null byte injection
    (r"\x00", "null byte injection"),
    (r"\\0", "escaped null byte"),
    # Quote escaping attacks
    (r"\\['\"]+.*[;|&]", "quote escape injection"),
    # Glob injection
    (r"\*\*/\.\.", "glob traversal"),
]

# SQL injection patterns (for any database operations)
SQL_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"'\s*(?:OR|AND)\s*'?\d*'?\s*=\s*'?\d*'?", "SQL OR/AND injection"),
    (r";\s*(?:DROP|DELETE|UPDATE|INSERT)", "SQL statement injection"),
    (r"--\s*$", "SQL comment injection"),
    (r"UNION\s+(?:ALL\s+)?SELECT", "SQL UNION injection"),
    (r"'\s*;\s*--", "SQL termination injection"),
]


# =============================================================================
# INPUT SANITIZATION
# =============================================================================


def sanitize_input(text: str, strict: bool = False) -> str:
    """
    Sanitize user input by removing or escaping dangerous characters.

    Args:
        text: Input text to sanitize
        strict: If True, apply stricter sanitization

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove other control characters (except newline and tab)
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    if strict:
        # Remove backticks
        text = text.replace("`", "'")
        # Remove $() command substitution
        text = re.sub(r"\$\([^)]*\)", "", text)
        # Escape semicolons
        text = text.replace(";", "\\;")
        # Escape ampersands
        text = text.replace("&&", "\\&\\&")
        text = text.replace("||", "\\|\\|")

    return text


def sanitize_path(path: str) -> str:
    """
    Sanitize a file path to prevent traversal attacks.

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path
    """
    if not path:
        return ""

    # Remove null bytes
    path = path.replace("\x00", "")

    # Normalize path separators
    path = path.replace("\\", "/")

    # Remove parent directory references
    while "../" in path:
        path = path.replace("../", "")
    while "/.." in path:
        path = path.replace("/..", "")

    # Remove double slashes
    while "//" in path:
        path = path.replace("//", "/")

    # Remove leading slashes for relative paths (optional, depends on use case)
    # path = path.lstrip("/")

    return path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove dangerous characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    if not filename:
        return ""

    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove null bytes and other dangerous chars
    filename = re.sub(r"[\x00-\x1f\x7f<>:\"|?*]", "", filename)

    # Prevent hidden files if needed
    filename = filename.lstrip(".")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


# =============================================================================
# COMMAND VALIDATION
# =============================================================================


class ValidationResult:
    """Result of input/command validation"""

    def __init__(self, is_valid: bool, message: str = "", threat_level: str = "none"):
        self.is_valid = is_valid
        self.message = message
        self.threat_level = threat_level  # none, low, medium, high, critical

    def __bool__(self):
        return self.is_valid

    def __repr__(self):
        return f"ValidationResult(valid={self.is_valid}, threat={self.threat_level}, msg='{self.message}')"


def validate_command(
    command: str, custom_blocked: Optional[Set[str]] = None
) -> ValidationResult:
    """
    Validate a command for safety before execution.

    Args:
        command: Command string to validate
        custom_blocked: Additional commands to block

    Returns:
        ValidationResult indicating if the command is safe
    """
    if not command or not command.strip():
        return ValidationResult(False, "Empty command", "low")

    command = command.strip()
    cmd_lower = command.lower()

    # Get the base command (first word)
    base_cmd = command.split()[0].split("/")[-1] if command.split() else ""

    # Check blocked commands
    blocked = BLOCKED_COMMANDS.copy()
    if custom_blocked:
        blocked.update(custom_blocked)

    if base_cmd.lower() in blocked:
        logger.warning(f"Blocked command: {base_cmd}")
        return ValidationResult(
            False, f"Command '{base_cmd}' is blocked for security reasons", "critical"
        )

    # Check for blocked commands anywhere in the command
    for blocked_cmd in blocked:
        if re.search(rf"\b{re.escape(blocked_cmd)}\b", cmd_lower):
            logger.warning(f"Blocked command found in chain: {blocked_cmd}")
            return ValidationResult(
                False,
                f"Command contains blocked operation: '{blocked_cmd}'",
                "critical",
            )

    # Check dangerous patterns
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected: {description}")
            return ValidationResult(
                False, f"Dangerous pattern detected: {description}", "critical"
            )

    # Check injection patterns
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, command):
            logger.warning(f"Injection attempt detected: {description}")
            return ValidationResult(
                False, f"Potential injection attack: {description}", "high"
            )

    return ValidationResult(True, "Command validated successfully", "none")


def validate_input(
    text: str,
    check_sql: bool = False,
    check_injection: bool = True,
    max_length: int = 10000,
) -> ValidationResult:
    """
    Validate user input for potential attacks.

    Args:
        text: Input text to validate
        check_sql: Whether to check for SQL injection
        check_injection: Whether to check for command injection
        max_length: Maximum allowed input length

    Returns:
        ValidationResult indicating if the input is safe
    """
    if not text:
        return ValidationResult(True, "Empty input", "none")

    # Length check
    if len(text) > max_length:
        return ValidationResult(
            False, f"Input exceeds maximum length of {max_length} characters", "medium"
        )

    # Check for null bytes
    if "\x00" in text:
        return ValidationResult(False, "Null byte detected in input", "high")

    # Check injection patterns
    if check_injection:
        for pattern, description in INJECTION_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Injection pattern in input: {description}")
                return ValidationResult(
                    False, f"Suspicious pattern in input: {description}", "high"
                )

    # Check SQL injection
    if check_sql:
        for pattern, description in SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"SQL injection pattern: {description}")
                return ValidationResult(
                    False, f"Potential SQL injection: {description}", "critical"
                )

    return ValidationResult(True, "Input validated successfully", "none")


# =============================================================================
# RESOURCE LIMITS
# =============================================================================


class ResourceLimits:
    """Configurable resource limits for agent execution"""

    def __init__(
        self,
        max_steps: int = 50,
        max_timeout: int = 300,
        max_output_size: int = 1024 * 1024,  # 1MB
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_memory_mb: int = 512,
        max_cpu_percent: int = 80,
    ):
        self.max_steps = max_steps
        self.max_timeout = max_timeout  # seconds
        self.max_output_size = max_output_size  # bytes
        self.max_file_size = max_file_size  # bytes
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_steps": self.max_steps,
            "max_timeout": self.max_timeout,
            "max_output_size": self.max_output_size,
            "max_file_size": self.max_file_size,
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceLimits":
        return cls(
            max_steps=data.get("max_steps", 50),
            max_timeout=data.get("max_timeout", 300),
            max_output_size=data.get("max_output_size", 1024 * 1024),
            max_file_size=data.get("max_file_size", 10 * 1024 * 1024),
            max_memory_mb=data.get("max_memory_mb", 512),
            max_cpu_percent=data.get("max_cpu_percent", 80),
        )


# Default resource limits
DEFAULT_LIMITS = ResourceLimits()

# Strict limits for untrusted agents
STRICT_LIMITS = ResourceLimits(
    max_steps=20,
    max_timeout=60,
    max_output_size=512 * 1024,  # 512KB
    max_file_size=1 * 1024 * 1024,  # 1MB
    max_memory_mb=256,
    max_cpu_percent=50,
)

# Relaxed limits for trusted agents
RELAXED_LIMITS = ResourceLimits(
    max_steps=200,
    max_timeout=600,
    max_output_size=10 * 1024 * 1024,  # 10MB
    max_file_size=100 * 1024 * 1024,  # 100MB
    max_memory_mb=2048,
    max_cpu_percent=95,
)


# =============================================================================
# SECURITY CONTEXT
# =============================================================================


class SecurityContext:
    """Security context for agent execution"""

    def __init__(
        self,
        blocked_commands: Optional[Set[str]] = None,
        resource_limits: Optional[ResourceLimits] = None,
        allow_network: bool = True,
        allow_file_write: bool = True,
        allow_file_read: bool = True,
        sandbox_mode: bool = False,
    ):
        self.blocked_commands = blocked_commands or BLOCKED_COMMANDS.copy()
        self.resource_limits = resource_limits or DEFAULT_LIMITS
        self.allow_network = allow_network
        self.allow_file_write = allow_file_write
        self.allow_file_read = allow_file_read
        self.sandbox_mode = sandbox_mode
        self._step_count = 0

    def increment_step(self) -> bool:
        """Increment step counter. Returns False if limit exceeded."""
        self._step_count += 1
        return self._step_count <= self.resource_limits.max_steps

    def get_step_count(self) -> int:
        """Get current step count."""
        return self._step_count

    def reset_steps(self):
        """Reset step counter."""
        self._step_count = 0

    def validate_command(self, command: str) -> ValidationResult:
        """Validate a command within this security context."""
        return validate_command(command, self.blocked_commands)

    def can_execute(self) -> Tuple[bool, str]:
        """Check if execution can continue."""
        if self._step_count >= self.resource_limits.max_steps:
            return False, f"Step limit ({self.resource_limits.max_steps}) exceeded"
        return True, "OK"
