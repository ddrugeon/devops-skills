"""Tests for run_yamllint module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_yamllint import YamllintRunner, run_yamllint, YAMLLINT_PATTERN, SEVERITY_MAP


class TestYamllintPattern:
    """Tests for the yamllint output regex pattern."""

    def test_matches_error_line(self):
        """Should match error lines from yamllint parsable output."""
        line = "/path/to/file.yml:10:5: [error] syntax error: expected <block end>"
        match = YAMLLINT_PATTERN.match(line)

        assert match is not None
        assert match.group("file") == "/path/to/file.yml"
        assert match.group("line") == "10"
        assert match.group("col") == "5"
        assert match.group("level") == "error"
        assert "syntax error" in match.group("message")

    def test_matches_warning_line(self):
        """Should match warning lines from yamllint parsable output."""
        line = "tasks/main.yml:1:1: [warning] missing document start"
        match = YAMLLINT_PATTERN.match(line)

        assert match is not None
        assert match.group("file") == "tasks/main.yml"
        assert match.group("level") == "warning"

    def test_no_match_invalid_line(self):
        """Should not match invalid lines."""
        invalid_lines = [
            "",
            "some random text",
            "file.yml:10: [error] missing column",
            "file.yml:10:5 [error] missing colon",
        ]
        for line in invalid_lines:
            assert YAMLLINT_PATTERN.match(line) is None


class TestSeverityMap:
    """Tests for SEVERITY_MAP."""

    def test_error_maps_to_critical(self):
        """Error severity should map to critical."""
        assert SEVERITY_MAP["error"] == "critical"

    def test_warning_maps_to_warning(self):
        """Warning severity should map to warning."""
        assert SEVERITY_MAP["warning"] == "warning"


class TestYamllintRunner:
    """Tests for YamllintRunner class."""

    def test_initialization(self):
        """Should initialize with correct tool name and hint."""
        runner = YamllintRunner()
        assert runner.tool_name == "yamllint"
        assert runner.installation_hint == "pip install yamllint"

    def test_build_command(self, tmp_role: Path):
        """Should build correct yamllint command."""
        runner = YamllintRunner()
        cmd = runner.build_command(tmp_role)

        assert cmd == ["yamllint", "-f", "parsable", str(tmp_role)]

    def test_normalize_severity_error(self):
        """Should normalize 'error' to 'critical'."""
        runner = YamllintRunner()
        assert runner.normalize_severity("error") == "critical"
        assert runner.normalize_severity("ERROR") == "critical"

    def test_normalize_severity_warning(self):
        """Should normalize 'warning' to 'warning'."""
        runner = YamllintRunner()
        assert runner.normalize_severity("warning") == "warning"
        assert runner.normalize_severity("WARNING") == "warning"

    def test_normalize_severity_unknown(self):
        """Should default to 'info' for unknown severities."""
        runner = YamllintRunner()
        assert runner.normalize_severity("unknown") == "info"
        assert runner.normalize_severity("fatal") == "info"

    def test_parse_output_empty(self, tmp_role: Path):
        """Should return empty list for empty output."""
        runner = YamllintRunner()
        result = runner.parse_output("", tmp_role)
        assert result == []

    def test_parse_output_single_finding(self, tmp_role: Path):
        """Should parse single finding correctly."""
        runner = YamllintRunner()
        stdout = f"{tmp_role}/tasks/main.yml:10:5: [error] syntax error: unexpected key"

        result = runner.parse_output(stdout, tmp_role)

        assert len(result) == 1
        assert result[0]["file"] == "tasks/main.yml"
        assert result[0]["line"] == 10
        assert result[0]["column"] == 5
        assert result[0]["severity"] == "critical"
        assert result[0]["rule"] == "yaml-syntax"
        assert "syntax error" in result[0]["message"]
        assert result[0]["tool"] == "yamllint"

    def test_parse_output_multiple_findings(self, tmp_role: Path):
        """Should parse multiple findings correctly."""
        runner = YamllintRunner()
        stdout = f"""{tmp_role}/tasks/main.yml:1:1: [warning] missing document start
{tmp_role}/tasks/main.yml:5:3: [error] syntax error
{tmp_role}/defaults/main.yml:2:10: [warning] trailing spaces"""

        result = runner.parse_output(stdout, tmp_role)

        assert len(result) == 3
        assert result[0]["severity"] == "warning"
        assert result[1]["severity"] == "critical"
        assert result[2]["severity"] == "warning"

    def test_parse_output_skips_malformed_lines(self, tmp_role: Path):
        """Should skip malformed lines and log warning."""
        runner = YamllintRunner()
        stdout = f"""invalid line here
{tmp_role}/tasks/main.yml:1:1: [error] valid error
another invalid line"""

        result = runner.parse_output(stdout, tmp_role)

        assert len(result) == 1
        assert result[0]["message"] == "valid error"


class TestRunYamllint:
    """Tests for run_yamllint function."""

    def test_returns_dict(self, tmp_role: Path):
        """Should return a dictionary."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = run_yamllint(str(tmp_role))

        assert isinstance(result, dict)
        assert "tool" in result
        assert result["tool"] == "yamllint"

    def test_path_not_exists(self, nonexistent_path: Path):
        """Should return error for non-existent path."""
        result = run_yamllint(str(nonexistent_path))

        assert result["error_type"] == "path_error"
        assert result["findings"] == []

    @patch("subprocess.run")
    def test_tool_not_found(self, mock_run, tmp_role: Path):
        """Should return error when yamllint is not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = run_yamllint(str(tmp_role))

        assert result["error_type"] == "missing_tool"
        assert "pip install yamllint" in result["installation_hint"]

    @patch("subprocess.run")
    def test_success_with_findings(self, mock_run, tmp_role: Path):
        """Should return findings on successful run."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=f"{tmp_role.resolve()}/tasks/main.yml:1:1: [warning] test warning",
            stderr="",
        )

        result = run_yamllint(str(tmp_role))

        assert "error" not in result
        assert len(result["findings"]) == 1
        assert result["summary"]["warning"] == 1
