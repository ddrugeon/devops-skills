"""Tests for run_ansiblelint module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_ansiblelint import AnsibleLintRunner, run_ansible_lint, SEVERITY_MAP


class TestSeverityMap:
    """Tests for SEVERITY_MAP."""

    def test_blocker_maps_to_critical(self):
        """Blocker severity should map to critical."""
        assert SEVERITY_MAP["blocker"] == "critical"

    def test_critical_maps_to_critical(self):
        """Critical severity should map to critical."""
        assert SEVERITY_MAP["critical"] == "critical"

    def test_major_maps_to_warning(self):
        """Major severity should map to warning."""
        assert SEVERITY_MAP["major"] == "warning"

    def test_minor_maps_to_warning(self):
        """Minor severity should map to warning."""
        assert SEVERITY_MAP["minor"] == "warning"

    def test_info_maps_to_info(self):
        """Info severity should map to info."""
        assert SEVERITY_MAP["info"] == "info"


class TestAnsibleLintRunner:
    """Tests for AnsibleLintRunner class."""

    def test_initialization(self):
        """Should initialize with correct tool name and hint."""
        runner = AnsibleLintRunner()
        assert runner.tool_name == "ansible-lint"
        assert runner.installation_hint == "pip install ansible-lint"

    def test_build_command(self, tmp_role: Path):
        """Should build correct ansible-lint command."""
        runner = AnsibleLintRunner()
        cmd = runner.build_command(tmp_role)

        assert cmd == ["ansible-lint", "-f", "json", "--nocolor", str(tmp_role)]

    def test_expected_return_codes(self):
        """Should expect return codes 0 and 2."""
        runner = AnsibleLintRunner()
        assert runner.get_expected_return_codes() == (0, 2)

    def test_normalize_severity_blocker(self):
        """Should normalize 'blocker' to 'critical'."""
        runner = AnsibleLintRunner()
        assert runner.normalize_severity("blocker") == "critical"
        assert runner.normalize_severity("BLOCKER") == "critical"

    def test_normalize_severity_major(self):
        """Should normalize 'major' to 'warning'."""
        runner = AnsibleLintRunner()
        assert runner.normalize_severity("major") == "warning"

    def test_normalize_severity_unknown(self):
        """Should default to 'info' for unknown severities."""
        runner = AnsibleLintRunner()
        assert runner.normalize_severity("unknown") == "info"

    def test_parse_output_empty(self, tmp_role: Path):
        """Should return empty list for empty output."""
        runner = AnsibleLintRunner()
        result = runner.parse_output("", tmp_role)
        assert result == []

    def test_parse_output_empty_array(self, tmp_role: Path):
        """Should return empty list for empty JSON array."""
        runner = AnsibleLintRunner()
        result = runner.parse_output("[]", tmp_role)
        assert result == []

    def test_parse_output_invalid_json(self, tmp_role: Path):
        """Should return empty list for invalid JSON."""
        runner = AnsibleLintRunner()
        result = runner.parse_output("not valid json", tmp_role)
        assert result == []

    def test_parse_output_single_finding(self, tmp_role: Path):
        """Should parse single finding correctly."""
        runner = AnsibleLintRunner()
        lint_output = json.dumps([{
            "severity": "major",
            "check_name": "yaml[truthy]",
            "description": "Truthy value should be one of [false, true]",
            "location": {
                "path": str(tmp_role / "tasks" / "main.yml"),
                "lines": {"begin": 5},
                "positions": {"begin": {"line": 5, "column": 10}},
            },
            "content": {"body": "Use 'true' instead of 'yes'"},
            "url": "https://ansible.readthedocs.io/projects/lint/rules/yaml/",
        }])

        result = runner.parse_output(lint_output, tmp_role)

        assert len(result) == 1
        assert result[0]["file"] == "tasks/main.yml"
        assert result[0]["line"] == 5
        assert result[0]["column"] == 10
        assert result[0]["severity"] == "warning"
        assert result[0]["rule"] == "yaml[truthy]"
        assert "Truthy value" in result[0]["message"]
        assert result[0]["suggestion"] == "Use 'true' instead of 'yes'"
        assert "ansible.readthedocs.io" in result[0]["url"]
        assert result[0]["tool"] == "ansible-lint"

    def test_parse_output_multiple_findings(self, tmp_role: Path):
        """Should parse multiple findings correctly."""
        runner = AnsibleLintRunner()
        lint_output = json.dumps([
            {
                "severity": "blocker",
                "check_name": "syntax-check",
                "description": "Syntax error",
                "location": {"path": str(tmp_role / "tasks" / "main.yml"), "lines": {"begin": 1}},
            },
            {
                "severity": "minor",
                "check_name": "name[missing]",
                "description": "Missing name",
                "location": {"path": str(tmp_role / "tasks" / "main.yml"), "lines": {"begin": 10}},
            },
        ])

        result = runner.parse_output(lint_output, tmp_role)

        assert len(result) == 2
        assert result[0]["severity"] == "critical"
        assert result[1]["severity"] == "warning"

    def test_parse_output_location_formats(self, tmp_role: Path):
        """Should handle different location formats."""
        runner = AnsibleLintRunner()

        # Test with lines.begin only
        output1 = json.dumps([{
            "severity": "info",
            "check_name": "test",
            "description": "Test",
            "location": {"path": str(tmp_role / "file.yml"), "lines": {"begin": 5}},
        }])
        result1 = runner.parse_output(output1, tmp_role)
        assert result1[0]["line"] == 5
        assert result1[0]["column"] is None

        # Test with positions.begin
        output2 = json.dumps([{
            "severity": "info",
            "check_name": "test",
            "description": "Test",
            "location": {
                "path": str(tmp_role / "file.yml"),
                "positions": {"begin": {"line": 10, "column": 3}},
            },
        }])
        result2 = runner.parse_output(output2, tmp_role)
        assert result2[0]["line"] == 10
        assert result2[0]["column"] == 3


class TestRunAnsibleLint:
    """Tests for run_ansible_lint function."""

    def test_returns_dict(self, tmp_role: Path):
        """Should return a dictionary."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")
            result = run_ansible_lint(str(tmp_role))

        assert isinstance(result, dict)
        assert result["tool"] == "ansible-lint"

    def test_path_not_exists(self, nonexistent_path: Path):
        """Should return error for non-existent path."""
        result = run_ansible_lint(str(nonexistent_path))

        assert result["error_type"] == "path_error"
        assert result["findings"] == []

    @patch("subprocess.run")
    def test_tool_not_found(self, mock_run, tmp_role: Path):
        """Should return error when ansible-lint is not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = run_ansible_lint(str(tmp_role))

        assert result["error_type"] == "missing_tool"
        assert "pip install ansible-lint" in result["installation_hint"]

    @patch("subprocess.run")
    def test_success_with_findings(self, mock_run, tmp_role: Path):
        """Should return findings on successful run."""
        lint_output = json.dumps([{
            "severity": "major",
            "check_name": "test-rule",
            "description": "Test finding",
            "location": {"path": str(tmp_role.resolve() / "tasks" / "main.yml"), "lines": {"begin": 1}},
        }])
        mock_run.return_value = MagicMock(
            returncode=2,
            stdout=lint_output,
            stderr="",
        )

        result = run_ansible_lint(str(tmp_role))

        assert "error" not in result
        assert len(result["findings"]) == 1
        assert result["summary"]["warning"] == 1
