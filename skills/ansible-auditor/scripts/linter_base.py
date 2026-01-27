#!/usr/bin/env python3
"""Shared base module for linter scripts.

This module provides common types, utilities, and configuration
used by all linter wrapper scripts (yamllint, ansible-lint, checkov).
"""

import logging
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypedDict, NotRequired

# Execution timeout in seconds (shared across all linters)
TIMEOUT_SECONDS = 300


def setup_logging(name: str) -> logging.Logger:
    """Configure logging to stderr (stdout is reserved for JSON output).

    Args:
        name: Logger name, typically __name__ from the calling module.

    Returns:
        Configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    return logging.getLogger(name)


class FindingDict(TypedDict, total=False):
    """Structure for a normalized finding.

    All linters produce findings with this common structure.
    Tool-specific fields (suggestion, url, description, resource) are optional.
    """

    file: str
    line: int | None
    column: int | None
    severity: str  # "critical", "warning", or "info"
    rule: str
    message: str
    tool: str
    # Optional tool-specific fields
    suggestion: str  # ansible-lint
    url: str  # ansible-lint
    description: str  # checkov
    resource: str  # checkov


class SummaryDict(TypedDict):
    """Summary of findings by severity."""

    critical: int
    warning: int
    info: int


class LinterResultDict(TypedDict, total=False):
    """Complete linter result structure.

    On success: tool, role_path, findings, summary
    On error: tool, error, error_type, findings (empty), optionally installation_hint
    """

    tool: str
    role_path: str
    findings: list[FindingDict]
    summary: SummaryDict
    error: str
    error_type: str  # "path_error", "missing_tool", "timeout", "parse_error"
    installation_hint: str


def normalize_path(file_path: str, role_path: Path, logger: logging.Logger) -> str:
    """Normalize file path to be relative to role path.

    Args:
        file_path: The file path to normalize (absolute or relative).
        role_path: The role root path to make paths relative to.
        logger: Logger for debug messages.

    Returns:
        Normalized relative path, or original path if normalization fails.
    """
    if not file_path:
        return ""
    try:
        path = Path(file_path)
        if path.is_absolute():
            return str(path.relative_to(role_path))
        # Handle paths like "home/user/test-role/..."
        abs_path = Path("/") / file_path
        return str(abs_path.relative_to(role_path))
    except ValueError:
        logger.debug("File %s is outside role path %s", file_path, role_path)
        return file_path


def build_summary(findings: list[FindingDict]) -> SummaryDict:
    """Build summary counts from findings list.

    Args:
        findings: List of finding dictionaries.

    Returns:
        Summary with counts by severity.
    """
    return {
        "critical": sum(1 for f in findings if f.get("severity") == "critical"),
        "warning": sum(1 for f in findings if f.get("severity") == "warning"),
        "info": sum(1 for f in findings if f.get("severity") == "info"),
    }


class BaseLinter(ABC):
    """Abstract base class for linter wrappers.

    Provides common execution logic with error handling for:
    - Path validation
    - Missing tool detection
    - Timeout handling
    - Result formatting
    """

    def __init__(self, tool_name: str, installation_hint: str):
        """Initialize the linter wrapper.

        Args:
            tool_name: Name of the linting tool (e.g., "yamllint").
            installation_hint: Pip install command hint.
        """
        self.tool_name = tool_name
        self.installation_hint = installation_hint
        self.logger = setup_logging(f"{__name__}.{tool_name}")

    @abstractmethod
    def build_command(self, role_path: Path) -> list[str]:
        """Build the command line arguments for the linter.

        Args:
            role_path: Resolved path to the Ansible role.

        Returns:
            List of command arguments.
        """
        pass

    @abstractmethod
    def parse_output(self, stdout: str, role_path: Path) -> list[FindingDict]:
        """Parse the linter output to findings list.

        Args:
            stdout: Standard output from the linter.
            role_path: Resolved path to the Ansible role.

        Returns:
            List of normalized findings.
        """
        pass

    def get_expected_return_codes(self) -> tuple[int, ...]:
        """Return codes that are considered normal (not errors).

        Override in subclasses if needed.
        Default: 0 (success) and 1 (findings found).
        """
        return (0, 1)

    def run(self, role_path: str) -> LinterResultDict:
        """Execute the linter and return structured results.

        Args:
            role_path: Path to the Ansible role to lint.

        Returns:
            Structured result with findings or error information.
        """
        resolved_path = Path(role_path).resolve()

        # Validate path exists
        if not resolved_path.exists():
            error_msg = f"Path does not exist: {resolved_path}"
            self.logger.error("%s: %s", self.tool_name, error_msg)
            return {
                "tool": self.tool_name,
                "error": error_msg,
                "error_type": "path_error",
                "findings": [],
            }

        cmd = self.build_command(resolved_path)

        # Execute with error handling
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except FileNotFoundError:
            error_msg = f"{self.tool_name} not found. Please install it first."
            self.logger.error("%s: %s", self.tool_name, error_msg)
            return {
                "tool": self.tool_name,
                "error": error_msg,
                "error_type": "missing_tool",
                "installation_hint": self.installation_hint,
                "findings": [],
            }
        except subprocess.TimeoutExpired:
            error_msg = f"Execution timeout after {TIMEOUT_SECONDS}s"
            self.logger.error("%s: %s", self.tool_name, error_msg)
            return {
                "tool": self.tool_name,
                "error": error_msg,
                "error_type": "timeout",
                "findings": [],
            }

        # Log unexpected return codes
        if result.returncode not in self.get_expected_return_codes():
            self.logger.warning(
                "%s returned code %d. stderr: %s",
                self.tool_name,
                result.returncode,
                result.stderr[:200] if result.stderr else "(empty)",
            )

        # Parse output
        findings = self.parse_output(result.stdout, resolved_path)

        # Build summary
        summary = build_summary(findings)

        self.logger.info(
            "%s: Found %d issues (critical=%d, warning=%d, info=%d)",
            self.tool_name,
            len(findings),
            summary["critical"],
            summary["warning"],
            summary["info"],
        )

        return {
            "tool": self.tool_name,
            "role_path": str(resolved_path),
            "findings": findings,
            "summary": summary,
        }
