#!/usr/bin/env python3
"""Unified runner for all Ansible role linters.

This script runs all configured linters (yamllint, ansible-lint, checkov)
on an Ansible role and aggregates the results into a single JSON output.

Usage:
    python run_all.py <role_path> [--config <config_file>]

Output format:
    {
        "role_path": "/path/to/role",
        "linters": {
            "yamllint": { ... },
            "ansible-lint": { ... },
            "checkov": { ... }
        },
        "summary": {
            "total_findings": N,
            "critical": N,
            "warning": N,
            "info": N,
            "linters_run": N,
            "linters_failed": N
        }
    }
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, NotRequired

from config import AuditConfig, load_config
from linter_base import LinterResultDict, SummaryDict, setup_logging
from run_ansiblelint import run_ansible_lint
from run_checkov import run_checkov
from run_yamllint import run_yamllint

logger = setup_logging(__name__)


class AggregatedSummary(TypedDict):
    """Summary of all linter results."""

    total_findings: int
    critical: int
    warning: int
    info: int
    linters_run: int
    linters_failed: int


class AggregatedResult(TypedDict):
    """Complete aggregated result structure."""

    role_path: str
    timestamp: str
    linters: dict[str, LinterResultDict]
    summary: AggregatedSummary
    config: NotRequired[dict]


def aggregate_summaries(results: dict[str, LinterResultDict]) -> AggregatedSummary:
    """Aggregate summaries from all linter results.

    Args:
        results: Dictionary of linter name to result.

    Returns:
        Aggregated summary counts.
    """
    total_critical = 0
    total_warning = 0
    total_info = 0
    linters_failed = 0

    for name, result in results.items():
        if "error" in result:
            linters_failed += 1
            continue

        summary = result.get("summary", {})
        total_critical += summary.get("critical", 0)
        total_warning += summary.get("warning", 0)
        total_info += summary.get("info", 0)

    return {
        "total_findings": total_critical + total_warning + total_info,
        "critical": total_critical,
        "warning": total_warning,
        "info": total_info,
        "linters_run": len(results),
        "linters_failed": linters_failed,
    }


def run_all_linters(
    role_path: str,
    config: AuditConfig | None = None,
) -> AggregatedResult:
    """Run all enabled linters and aggregate results.

    Args:
        role_path: Path to the Ansible role to lint.
        config: Optional configuration, uses defaults if None.

    Returns:
        Aggregated results from all linters.
    """
    if config is None:
        config = AuditConfig()

    resolved_path = Path(role_path).resolve()
    results: dict[str, LinterResultDict] = {}

    # Run yamllint if enabled
    if config.yamllint.enabled:
        logger.info("Running yamllint...")
        results["yamllint"] = run_yamllint(str(resolved_path))

    # Run ansible-lint if enabled
    if config.ansible_lint.enabled:
        logger.info("Running ansible-lint...")
        results["ansible-lint"] = run_ansible_lint(str(resolved_path))

    # Run checkov if enabled
    if config.checkov.enabled:
        logger.info("Running checkov...")
        results["checkov"] = run_checkov(str(resolved_path))

    # Aggregate results
    summary = aggregate_summaries(results)

    logger.info(
        "Audit complete: %d total findings (critical=%d, warning=%d, info=%d)",
        summary["total_findings"],
        summary["critical"],
        summary["warning"],
        summary["info"],
    )

    if summary["linters_failed"] > 0:
        logger.warning(
            "%d of %d linters failed to run",
            summary["linters_failed"],
            summary["linters_run"],
        )

    return {
        "role_path": str(resolved_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "linters": results,
        "summary": summary,
    }


def main() -> int:
    """Main entry point for CLI usage.

    Returns:
        Exit code (0 for success, 1 for findings, 2 for errors).
    """
    parser = argparse.ArgumentParser(
        description="Run all Ansible role linters and aggregate results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s /path/to/role
    %(prog)s /path/to/role --config audit-config.json
    %(prog)s /path/to/role --no-yamllint --no-checkov
    %(prog)s /path/to/role --fail-on-error
        """,
    )
    parser.add_argument(
        "role_path",
        help="Path to the Ansible role to audit",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to configuration file (JSON or YAML)",
    )
    parser.add_argument(
        "--no-yamllint",
        action="store_true",
        help="Disable yamllint",
    )
    parser.add_argument(
        "--no-ansible-lint",
        action="store_true",
        help="Disable ansible-lint",
    )
    parser.add_argument(
        "--no-checkov",
        action="store_true",
        help="Disable checkov",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 if any findings are detected",
    )
    parser.add_argument(
        "--include-config",
        action="store_true",
        help="Include configuration in output",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override from command line flags
    if args.no_yamllint:
        config.yamllint.enabled = False
    if args.no_ansible_lint:
        config.ansible_lint.enabled = False
    if args.no_checkov:
        config.checkov.enabled = False
    if args.fail_on_error:
        config.fail_on_error = True

    # Validate role path
    role_path = Path(args.role_path)
    if not role_path.exists():
        error_result = {
            "error": f"Role path does not exist: {role_path}",
            "error_type": "path_error",
        }
        print(json.dumps(error_result, indent=2))
        return 2

    # Run all linters
    result = run_all_linters(str(role_path), config)

    # Optionally include config in output
    if args.include_config:
        result["config"] = config.to_dict()

    # Output JSON
    print(json.dumps(result, indent=2))

    # Determine exit code
    if config.fail_on_error and result["summary"]["total_findings"] > 0:
        return 1

    if result["summary"]["linters_failed"] == result["summary"]["linters_run"]:
        return 2  # All linters failed

    return 0


if __name__ == "__main__":
    sys.exit(main())
