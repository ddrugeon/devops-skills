#!/usr/bin/env python3
"""Configuration module for linter scripts.

This module centralizes all configuration values that can be
customized for different environments or use cases.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Type alias for severity levels
SeverityLevel = Literal["critical", "warning", "info"]

# Default execution timeout in seconds
DEFAULT_TIMEOUT_SECONDS = 300

# Severity mappings for each linter
YAMLLINT_SEVERITY_MAP: dict[str, SeverityLevel] = {
    "error": "critical",
    "warning": "warning",
}

ANSIBLE_LINT_SEVERITY_MAP: dict[str, SeverityLevel] = {
    "blocker": "critical",
    "critical": "critical",
    "major": "warning",
    "minor": "warning",
    "info": "info",
}

CHECKOV_SEVERITY_MAP: dict[str, SeverityLevel] = {
    "CRITICAL": "critical",
    "HIGH": "critical",
    "MEDIUM": "warning",
    "LOW": "info",
    "UNKNOWN": "info",
}


@dataclass
class LinterConfig:
    """Configuration for a single linter.

    Attributes:
        enabled: Whether this linter should be run.
        timeout: Execution timeout in seconds.
        extra_args: Additional command-line arguments to pass.
    """

    enabled: bool = True
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    extra_args: list[str] = field(default_factory=list)


@dataclass
class AuditConfig:
    """Configuration for the entire audit process.

    Attributes:
        yamllint: Configuration for yamllint.
        ansible_lint: Configuration for ansible-lint.
        checkov: Configuration for checkov.
        parallel: Whether to run linters in parallel (future use).
        fail_on_error: Whether to exit with error code if findings exist.
    """

    yamllint: LinterConfig = field(default_factory=LinterConfig)
    ansible_lint: LinterConfig = field(default_factory=LinterConfig)
    checkov: LinterConfig = field(default_factory=LinterConfig)
    parallel: bool = False
    fail_on_error: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "AuditConfig":
        """Create config from dictionary (e.g., from JSON/YAML file).

        Args:
            data: Configuration dictionary.

        Returns:
            AuditConfig instance.
        """
        config = cls()

        if "yamllint" in data:
            config.yamllint = LinterConfig(**data["yamllint"])
        if "ansible_lint" in data:
            config.ansible_lint = LinterConfig(**data["ansible_lint"])
        if "checkov" in data:
            config.checkov = LinterConfig(**data["checkov"])
        if "parallel" in data:
            config.parallel = data["parallel"]
        if "fail_on_error" in data:
            config.fail_on_error = data["fail_on_error"]

        return config

    def to_dict(self) -> dict:
        """Convert config to dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "yamllint": {
                "enabled": self.yamllint.enabled,
                "timeout": self.yamllint.timeout,
                "extra_args": self.yamllint.extra_args,
            },
            "ansible_lint": {
                "enabled": self.ansible_lint.enabled,
                "timeout": self.ansible_lint.timeout,
                "extra_args": self.ansible_lint.extra_args,
            },
            "checkov": {
                "enabled": self.checkov.enabled,
                "timeout": self.checkov.timeout,
                "extra_args": self.checkov.extra_args,
            },
            "parallel": self.parallel,
            "fail_on_error": self.fail_on_error,
        }


def load_config(config_path: Path | None = None) -> AuditConfig:
    """Load configuration from file or return defaults.

    Supports JSON and YAML formats (based on file extension).

    Args:
        config_path: Path to configuration file, or None for defaults.

    Returns:
        AuditConfig instance.
    """
    if config_path is None:
        return AuditConfig()

    if not config_path.exists():
        return AuditConfig()

    import json

    content = config_path.read_text()

    if config_path.suffix in (".yml", ".yaml"):
        try:
            import yaml

            data = yaml.safe_load(content)
        except ImportError:
            # Fall back to JSON if PyYAML not installed
            data = json.loads(content)
    else:
        data = json.loads(content)

    return AuditConfig.from_dict(data or {})
