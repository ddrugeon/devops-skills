"""Ansible auditor linter scripts.

This package provides wrapper scripts for running linting tools
on Ansible roles and producing normalized JSON output.

Available linters:
- yamllint: YAML syntax validation
- ansible-lint: Ansible best practices
- checkov: Security and compliance scanning

Usage:
    # Run individual linters
    from scripts import run_yamllint, run_ansible_lint, run_checkov
    result = run_yamllint("/path/to/role")

    # Run all linters at once
    from scripts import run_all_linters
    result = run_all_linters("/path/to/role")

    # With custom configuration
    from scripts import run_all_linters, AuditConfig
    config = AuditConfig()
    config.checkov.enabled = False
    result = run_all_linters("/path/to/role", config)
"""

from .config import (
    AuditConfig,
    LinterConfig,
    load_config,
    DEFAULT_TIMEOUT_SECONDS,
    YAMLLINT_SEVERITY_MAP,
    ANSIBLE_LINT_SEVERITY_MAP,
    CHECKOV_SEVERITY_MAP,
)
from .linter_base import (
    BaseLinter,
    FindingDict,
    LinterResultDict,
    SummaryDict,
    TIMEOUT_SECONDS,
    build_summary,
    normalize_path,
    setup_logging,
)
from .run_ansiblelint import run_ansible_lint
from .run_checkov import run_checkov
from .run_yamllint import run_yamllint
from .run_all import run_all_linters, aggregate_summaries

__all__ = [
    # Configuration
    "AuditConfig",
    "LinterConfig",
    "load_config",
    "DEFAULT_TIMEOUT_SECONDS",
    "YAMLLINT_SEVERITY_MAP",
    "ANSIBLE_LINT_SEVERITY_MAP",
    "CHECKOV_SEVERITY_MAP",
    # Base classes and types
    "BaseLinter",
    "FindingDict",
    "LinterResultDict",
    "SummaryDict",
    # Utilities
    "TIMEOUT_SECONDS",
    "build_summary",
    "normalize_path",
    "setup_logging",
    "aggregate_summaries",
    # Runner functions
    "run_ansible_lint",
    "run_checkov",
    "run_yamllint",
    "run_all_linters",
]
