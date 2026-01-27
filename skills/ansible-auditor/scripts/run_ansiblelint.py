#!/usr/bin/env python3
"""Run ansible-lint on Ansible role and output JSON results."""

import json
import sys
from pathlib import Path

from linter_base import (
    BaseLinter,
    FindingDict,
    LinterResultDict,
    normalize_path,
)

# Mapping ansible-lint severity to our standard levels
SEVERITY_MAP = {
    "blocker": "critical",
    "critical": "critical",
    "major": "warning",
    "minor": "warning",
    "info": "info",
}


class AnsibleLintRunner(BaseLinter):
    """Ansible-lint linter wrapper."""

    def __init__(self):
        super().__init__(
            tool_name="ansible-lint",
            installation_hint="pip install ansible-lint",
        )

    def build_command(self, role_path: Path) -> list[str]:
        """Build ansible-lint command with JSON output format."""
        return ["ansible-lint", "-f", "json", "--nocolor", str(role_path)]

    def get_expected_return_codes(self) -> tuple[int, ...]:
        """ansible-lint returns 2 when findings are found."""
        return (0, 2)

    def normalize_severity(self, level: str) -> str:
        """Normalize ansible-lint severity to standard levels."""
        normalized = SEVERITY_MAP.get(level.lower())
        if normalized is None:
            self.logger.warning(
                "Unknown ansible-lint severity: %s, defaulting to info", level
            )
            return "info"
        return normalized

    def parse_output(self, stdout: str, role_path: Path) -> list[FindingDict]:
        """Parse ansible-lint JSON output to findings list."""
        findings: list[FindingDict] = []

        # ansible-lint returns JSON array on stdout
        try:
            lint_results = json.loads(stdout) if stdout.strip() else []
        except json.JSONDecodeError as e:
            self.logger.warning("Failed to parse ansible-lint JSON output: %s", e)
            return findings

        for item in lint_results:
            severity = self.normalize_severity(item.get("severity", "info"))

            # Handle location - can be in different formats
            location = item.get("location", {})
            file_path = location.get("path", "")

            # Get line number from either lines.begin or positions.begin.line
            line_num = None
            if "lines" in location:
                line_num = location["lines"].get("begin")
            elif "positions" in location:
                line_num = location["positions"].get("begin", {}).get("line")

            # Get column if available
            col_num = None
            if "positions" in location:
                col_num = location["positions"].get("begin", {}).get("column")

            # Get suggestion from content.body if available
            suggestion = item.get("content", {}).get("body", "")

            findings.append({
                "file": normalize_path(file_path, role_path, self.logger),
                "line": line_num,
                "column": col_num,
                "severity": severity,
                "rule": item.get("check_name", "unknown"),
                "message": item.get("description", ""),
                "suggestion": suggestion,
                "url": item.get("url", ""),
                "tool": "ansible-lint",
            })

        return findings


def run_ansible_lint(role_path: str) -> LinterResultDict:
    """Execute ansible-lint and return structured results.

    Args:
        role_path: Path to the Ansible role to lint.

    Returns:
        Structured result with findings or error information.
    """
    runner = AnsibleLintRunner()
    return runner.run(role_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: run_ansiblelint.py <role_path>"}))
        sys.exit(1)

    results = run_ansible_lint(sys.argv[1])
    print(json.dumps(results, indent=2))
