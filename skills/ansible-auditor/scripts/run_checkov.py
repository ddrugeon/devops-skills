#!/usr/bin/env python3
"""Run checkov on Ansible role and output JSON results."""

import json
import sys
from pathlib import Path

from linter_base import (
    BaseLinter,
    FindingDict,
    LinterResultDict,
)

# Mapping checkov severity to our standard levels
SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "critical",
    "MEDIUM": "warning",
    "LOW": "info",
    "UNKNOWN": "info",
}


class CheckovRunner(BaseLinter):
    """Checkov linter wrapper."""

    def __init__(self):
        super().__init__(
            tool_name="checkov",
            installation_hint="pip install checkov",
        )

    def build_command(self, role_path: Path) -> list[str]:
        """Build checkov command with JSON output format for Ansible."""
        return [
            "checkov",
            "-d", str(role_path),
            "--framework", "ansible",
            "-o", "json",
            "--compact",
        ]

    def normalize_severity(self, level: str) -> str:
        """Normalize checkov severity to standard levels."""
        normalized = SEVERITY_MAP.get(level.upper())
        if normalized is None:
            self.logger.warning(
                "Unknown checkov severity: %s, defaulting to info", level
            )
            return "info"
        return normalized

    def parse_output(self, stdout: str, role_path: Path) -> list[FindingDict]:
        """Parse checkov JSON output to findings list."""
        findings: list[FindingDict] = []

        try:
            # checkov can return a single object or array
            checkov_output = json.loads(stdout) if stdout.strip() else {}

            # Handle both single result and array of results
            if isinstance(checkov_output, list):
                results_list = checkov_output
            else:
                results_list = [checkov_output]

            for checkov_result in results_list:
                failed_checks = checkov_result.get("results", {}).get("failed_checks", [])

                for check in failed_checks:
                    severity = self.normalize_severity(check.get("severity", "UNKNOWN"))

                    file_path = check.get("file_path", "")
                    # Remove leading / if present
                    if file_path.startswith("/"):
                        file_path = file_path[1:]

                    findings.append({
                        "file": file_path,
                        "line": check.get("file_line_range", [None])[0],
                        "column": None,
                        "severity": severity,
                        "rule": check.get("check_id", "unknown"),
                        "message": check.get("check_name", ""),
                        "description": check.get("guideline", ""),
                        "resource": check.get("resource", ""),
                        "tool": "checkov",
                    })

        except json.JSONDecodeError as e:
            self.logger.warning("Failed to parse checkov JSON output: %s", e)

        return findings


def run_checkov(role_path: str) -> LinterResultDict:
    """Execute checkov and return structured results.

    Args:
        role_path: Path to the Ansible role to lint.

    Returns:
        Structured result with findings or error information.
    """
    runner = CheckovRunner()
    return runner.run(role_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: run_checkov.py <role_path>"}))
        sys.exit(1)

    results = run_checkov(sys.argv[1])
    print(json.dumps(results, indent=2))
