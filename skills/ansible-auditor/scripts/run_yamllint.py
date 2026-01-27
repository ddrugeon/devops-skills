#!/usr/bin/env python3
"""Run yamllint on Ansible role and output JSON results."""

import json
import re
import sys
from pathlib import Path

from linter_base import (
    BaseLinter,
    FindingDict,
    LinterResultDict,
    normalize_path,
)

# Regex pattern for yamllint parsable output
# Format: file:line:col: [level] message (rule)
YAMLLINT_PATTERN = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+):\s*\[(?P<level>error|warning)\]\s*(?P<message>.+)$"
)

# Mapping yamllint severity to our standard levels
SEVERITY_MAP = {
    "error": "critical",
    "warning": "warning",
}


class YamllintRunner(BaseLinter):
    """Yamllint linter wrapper."""

    def __init__(self):
        super().__init__(
            tool_name="yamllint",
            installation_hint="pip install yamllint",
        )

    def build_command(self, role_path: Path) -> list[str]:
        """Build yamllint command with parsable output format."""
        return ["yamllint", "-f", "parsable", str(role_path)]

    def normalize_severity(self, level: str) -> str:
        """Normalize yamllint severity to standard levels."""
        normalized = SEVERITY_MAP.get(level.lower())
        if normalized is None:
            self.logger.warning(
                "Unknown yamllint severity: %s, defaulting to info", level
            )
            return "info"
        return normalized

    def parse_output(self, stdout: str, role_path: Path) -> list[FindingDict]:
        """Parse yamllint parsable output to findings list."""
        findings: list[FindingDict] = []
        skipped_lines = 0

        for line in stdout.strip().split("\n"):
            if not line:
                continue

            match = YAMLLINT_PATTERN.match(line)
            if match:
                groups = match.groupdict()
                findings.append({
                    "file": normalize_path(groups["file"], role_path, self.logger),
                    "line": int(groups["line"]),
                    "column": int(groups["col"]),
                    "severity": self.normalize_severity(groups["level"]),
                    "rule": "yaml-syntax",
                    "message": groups["message"].strip(),
                    "tool": "yamllint",
                })
            else:
                skipped_lines += 1
                self.logger.debug("Skipped malformed line: %s", line[:100])

        if skipped_lines > 0:
            self.logger.warning("yamllint: Skipped %d malformed lines", skipped_lines)

        return findings


def run_yamllint(role_path: str) -> LinterResultDict:
    """Execute yamllint and return structured results.

    Args:
        role_path: Path to the Ansible role to lint.

    Returns:
        Structured result with findings or error information.
    """
    runner = YamllintRunner()
    return runner.run(role_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: run_yamllint.py <role_path>"}))
        sys.exit(1)

    results = run_yamllint(sys.argv[1])
    print(json.dumps(results, indent=2))
