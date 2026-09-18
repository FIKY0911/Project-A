import re
from typing import Optional, Tuple

FORBIDDEN_TOKENS = [
    "rm -rf",
    "del /f",
    "del /s",
    "del /q",
    "format ",
    "dd if=",
    "mkfs",
    ":(){ :|:& };:",
    "chmod -R 777 /",
    "shutdown -s",
    "init 0",
    "reboot",
    "drop database",
]

FORBIDDEN_PATHS = [
    r"c:\\windows",
    r"c:\\windows\\system32",
    r"/etc",
    r"/boot",
    r"/sys",
    r"/proc",
    r"~/.ssh",
    r"/root",
]

class OSProtectionGuardrail:
    """
    Validates automated commands and file operations against dangerous destructive patterns.
    """
    @classmethod
    def check_command(cls, command_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Returns (is_violation, violation_code, matched_token)
        """
        if not command_str:
            return False, None, None

        cmd_lower = command_str.lower()
        for token in FORBIDDEN_TOKENS:
            if token in cmd_lower:
                return True, "FORBIDDEN_OS_COMMAND", token

        for path in FORBIDDEN_PATHS:
            if path in cmd_lower:
                return True, "FORBIDDEN_RESTRICTED_PATH", path

        return False, None, None
