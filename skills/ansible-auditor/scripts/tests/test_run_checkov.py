"""Tests for run_checkov module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_checkov import CheckovRunner, run_checkov, SEVERITY_MAP


class TestSeverityMap:
    """Tests for SEVERITY_MAP."""

    def test_critical_maps_to_critical(self):
        """CRITICAL severity should map to critical."""
        assert SEVERITY_MAP["CRITICAL"] == "critical"

    def test_high_maps_to_critical(self):
        """HIGH severity should map to critical."""
        assert SEVERITY_MAP["HIGH"] == "critical"

    def test_medium_maps_to_warning(self):
        """MEDIUM severity should map to warning."""
        assert SEVERITY_MAP["MEDIUM"] == "warning"

    def test_low_maps_to_info(self):
        """LOW severity should map to info."""
        assert SEVERITY_MAP["LOW"] == "info"

    def test_unknown_maps_to_info(self):
        """UNKNOWN severity should map to info."""
        assert SEVERITY_MAP["UNKNOWN"] == "info"


class TestCheckovRunner:
    """Tests for CheckovRunner class."""

    def test_initialization(self):
        """Should initialize with correct tool name and hint."""
        runner = CheckovRunner()
        assert runner.tool_name == "checkov"
        assert runner.installation_hint == "pip install checkov"

    def test_build_command(self, tmp_role: Path):
        """Should build correct checkov command."""
        runner = CheckovRunner()
        cmd = runner.build_command(tmp_role)

        assert cmd == [
            "checkov",
            "-d", str(tmp_role),
            "--framework", "ansible",
            "-o", "json",
            "--compact",
        ]

    def test_normalize_severity_critical(self):
        """Should normalize 'CRITICAL' to 'critical'."""
        runner = CheckovRunner()
        assert runner.normalize_severity("CRITICAL") == "critical"
        assert runner.normalize_severity("critical") == "critical"

    def test_normalize_severity_high(self):
        """Should normalize 'HIGH' to 'critical'."""
        runner = CheckovRunner()
        assert runner.normalize_severity("HIGH") == "critical"
        assert runner.normalize_severity("high") == "critical"

    def test_normalize_severity_medium(self):
        """Should normalize 'MEDIUM' to 'warning'."""
        runner = CheckovRunner()
        assert runner.normalize_severity("MEDIUM") == "warning"

    def test_normalize_severity_unknown(self):
        """Should default to 'info' for unknown severities."""
        runner = CheckovRunner()
        assert runner.normalize_severity("UNKNOWN") == "info"
        assert runner.normalize_severity("something_else") == "info"

    def test_parse_output_empty(self, tmp_role: Path):
        """Should return empty list for empty output."""
        runner = CheckovRunner()
        result = runner.parse_output("", tmp_role)
        assert result == []

    def test_parse_output_empty_object(self, tmp_role: Path):
        """Should return empty list for empty JSON object."""
        runner = CheckovRunner()
        result = runner.parse_output("{}", tmp_role)
        assert result == []

    def test_parse_output_invalid_json(self, tmp_role: Path):
        """Should return empty list for invalid JSON."""
        runner = CheckovRunner()
        result = runner.parse_output("not valid json", tmp_role)
        assert result == []

    def test_parse_output_single_finding(self, tmp_role: Path):
        """Should parse single finding correctly."""
        runner = CheckovRunner()
        checkov_output = json.dumps({
            "results": {
                "failed_checks": [{
                    "check_id": "CKV_ANSIBLE_1",
                    "check_name": "Ensure that HTTPS is used for web servers",
                    "severity": "HIGH",
                    "file_path": "/tasks/main.yml",
                    "file_line_range": [10, 15],
                    "guideline": "https://docs.checkov.io/...",
                    "resource": "tasks.Configure webserver",
                }]
            }
        })

        result = runner.parse_output(checkov_output, tmp_role)

        assert len(result) == 1
        assert result[0]["file"] == "tasks/main.yml"  # Leading / removed
        assert result[0]["line"] == 10
        assert result[0]["column"] is None
        assert result[0]["severity"] == "critical"
        assert result[0]["rule"] == "CKV_ANSIBLE_1"
        assert "HTTPS" in result[0]["message"]
        assert "checkov.io" in result[0]["description"]
        assert result[0]["resource"] == "tasks.Configure webserver"
        assert result[0]["tool"] == "checkov"

    def test_parse_output_multiple_findings(self, tmp_role: Path):
        """Should parse multiple findings correctly."""
        runner = CheckovRunner()
        checkov_output = json.dumps({
            "results": {
                "failed_checks": [
                    {
                        "check_id": "CKV_ANSIBLE_1",
                        "check_name": "Check 1",
                        "severity": "CRITICAL",
                        "file_path": "/tasks/main.yml",
                        "file_line_range": [1, 5],
                    },
                    {
                        "check_id": "CKV_ANSIBLE_2",
                        "check_name": "Check 2",
                        "severity": "MEDIUM",
                        "file_path": "/tasks/main.yml",
                        "file_line_range": [10, 15],
                    },
                    {
                        "check_id": "CKV_ANSIBLE_3",
                        "check_name": "Check 3",
                        "severity": "LOW",
                        "file_path": "/handlers/main.yml",
                        "file_line_range": [1, 3],
                    },
                ]
            }
        })

        result = runner.parse_output(checkov_output, tmp_role)

        assert len(result) == 3
        assert result[0]["severity"] == "critical"
        assert result[1]["severity"] == "warning"
        assert result[2]["severity"] == "info"

    def test_parse_output_array_format(self, tmp_role: Path):
        """Should handle array format from checkov (multiple frameworks)."""
        runner = CheckovRunner()
        checkov_output = json.dumps([
            {
                "check_type": "ansible",
                "results": {
                    "failed_checks": [{
                        "check_id": "CKV_ANSIBLE_1",
                        "check_name": "Test check",
                        "severity": "HIGH",
                        "file_path": "/tasks/main.yml",
                        "file_line_range": [1, 5],
                    }]
                }
            }
        ])

        result = runner.parse_output(checkov_output, tmp_role)

        assert len(result) == 1
        assert result[0]["rule"] == "CKV_ANSIBLE_1"

    def test_parse_output_no_failed_checks(self, tmp_role: Path):
        """Should return empty list when no failed checks."""
        runner = CheckovRunner()
        checkov_output = json.dumps({
            "results": {
                "passed_checks": [{"check_id": "CKV_ANSIBLE_1"}],
                "failed_checks": [],
            }
        })

        result = runner.parse_output(checkov_output, tmp_role)
        assert result == []

    def test_parse_output_missing_severity(self, tmp_role: Path):
        """Should handle missing severity field."""
        runner = CheckovRunner()
        checkov_output = json.dumps({
            "results": {
                "failed_checks": [{
                    "check_id": "CKV_ANSIBLE_1",
                    "check_name": "Test check",
                    "file_path": "/tasks/main.yml",
                    "file_line_range": [1, 5],
                    # No severity field
                }]
            }
        })

        result = runner.parse_output(checkov_output, tmp_role)

        assert len(result) == 1
        assert result[0]["severity"] == "info"  # Default for UNKNOWN


class TestRunCheckov:
    """Tests for run_checkov function."""

    def test_returns_dict(self, tmp_role: Path):
        """Should return a dictionary."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")
            result = run_checkov(str(tmp_role))

        assert isinstance(result, dict)
        assert result["tool"] == "checkov"

    def test_path_not_exists(self, nonexistent_path: Path):
        """Should return error for non-existent path."""
        result = run_checkov(str(nonexistent_path))

        assert result["error_type"] == "path_error"
        assert result["findings"] == []

    @patch("subprocess.run")
    def test_tool_not_found(self, mock_run, tmp_role: Path):
        """Should return error when checkov is not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = run_checkov(str(tmp_role))

        assert result["error_type"] == "missing_tool"
        assert "pip install checkov" in result["installation_hint"]

    @patch("subprocess.run")
    def test_success_with_findings(self, mock_run, tmp_role: Path):
        """Should return findings on successful run."""
        checkov_output = json.dumps({
            "results": {
                "failed_checks": [{
                    "check_id": "CKV_ANSIBLE_1",
                    "check_name": "Test check",
                    "severity": "HIGH",
                    "file_path": "/tasks/main.yml",
                    "file_line_range": [1, 5],
                }]
            }
        })
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=checkov_output,
            stderr="",
        )

        result = run_checkov(str(tmp_role))

        assert "error" not in result
        assert len(result["findings"]) == 1
        assert result["summary"]["critical"] == 1
