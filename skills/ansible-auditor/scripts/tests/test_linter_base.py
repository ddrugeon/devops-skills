"""Tests for linter_base module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from linter_base import (
    BaseLinter,
    FindingDict,
    SummaryDict,
    build_summary,
    normalize_path,
    setup_logging,
    TIMEOUT_SECONDS,
)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_returns_logger(self):
        """Should return a logger instance."""
        logger = setup_logging("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_logger_can_log(self):
        """Should be able to log messages."""
        logger = setup_logging("test_log")
        # Should not raise
        logger.info("Test message")
        logger.warning("Warning message")
        logger.error("Error message")


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_empty_path(self, tmp_path: Path):
        """Should return empty string for empty path."""
        logger = MagicMock()
        result = normalize_path("", tmp_path, logger)
        assert result == ""

    def test_absolute_path_inside_role(self, tmp_path: Path):
        """Should return relative path for absolute path inside role."""
        logger = MagicMock()
        file_path = str(tmp_path / "tasks" / "main.yml")
        result = normalize_path(file_path, tmp_path, logger)
        assert result == "tasks/main.yml"

    def test_absolute_path_outside_role(self, tmp_path: Path):
        """Should return original path for absolute path outside role."""
        logger = MagicMock()
        result = normalize_path("/etc/passwd", tmp_path, logger)
        assert result == "/etc/passwd"
        logger.debug.assert_called_once()

    def test_relative_path_reconstruction(self, tmp_path: Path):
        """Should handle paths like 'home/user/role/file'."""
        logger = MagicMock()
        # Create a path that looks like it came from a relative-ish format
        role_path = Path("/home/user/role")
        result = normalize_path("home/user/role/tasks/main.yml", role_path, logger)
        assert result == "tasks/main.yml"


class TestBuildSummary:
    """Tests for build_summary function."""

    def test_empty_findings(self):
        """Should return zeros for empty findings."""
        result = build_summary([])
        assert result == {"critical": 0, "warning": 0, "info": 0}

    def test_counts_by_severity(self):
        """Should correctly count findings by severity."""
        findings: list[FindingDict] = [
            {"file": "a.yml", "severity": "critical", "rule": "r1", "message": "m1", "tool": "t"},
            {"file": "b.yml", "severity": "critical", "rule": "r2", "message": "m2", "tool": "t"},
            {"file": "c.yml", "severity": "warning", "rule": "r3", "message": "m3", "tool": "t"},
            {"file": "d.yml", "severity": "info", "rule": "r4", "message": "m4", "tool": "t"},
            {"file": "e.yml", "severity": "info", "rule": "r5", "message": "m5", "tool": "t"},
            {"file": "f.yml", "severity": "info", "rule": "r6", "message": "m6", "tool": "t"},
        ]
        result = build_summary(findings)
        assert result == {"critical": 2, "warning": 1, "info": 3}

    def test_missing_severity_field(self):
        """Should handle findings without severity field."""
        findings = [{"file": "a.yml", "rule": "r1", "message": "m1", "tool": "t"}]
        result = build_summary(findings)
        assert result == {"critical": 0, "warning": 0, "info": 0}


class ConcreteTestLinter(BaseLinter):
    """Concrete implementation for testing BaseLinter."""

    def __init__(self):
        super().__init__(tool_name="test-linter", installation_hint="pip install test-linter")
        self.mock_findings: list[FindingDict] = []

    def build_command(self, role_path: Path) -> list[str]:
        return ["test-linter", str(role_path)]

    def parse_output(self, stdout: str, role_path: Path) -> list[FindingDict]:
        return self.mock_findings


class TestBaseLinter:
    """Tests for BaseLinter abstract class."""

    def test_initialization(self):
        """Should initialize with tool name and installation hint."""
        linter = ConcreteTestLinter()
        assert linter.tool_name == "test-linter"
        assert linter.installation_hint == "pip install test-linter"
        assert linter.logger is not None

    def test_default_expected_return_codes(self):
        """Should return (0, 1) by default."""
        linter = ConcreteTestLinter()
        assert linter.get_expected_return_codes() == (0, 1)

    def test_run_path_not_exists(self, nonexistent_path: Path):
        """Should return path_error when path doesn't exist."""
        linter = ConcreteTestLinter()
        result = linter.run(str(nonexistent_path))

        assert result["tool"] == "test-linter"
        assert result["error_type"] == "path_error"
        assert "does not exist" in result["error"]
        assert result["findings"] == []

    @patch("subprocess.run")
    def test_run_tool_not_found(self, mock_run, tmp_role: Path):
        """Should return missing_tool when tool is not installed."""
        mock_run.side_effect = FileNotFoundError()

        linter = ConcreteTestLinter()
        result = linter.run(str(tmp_role))

        assert result["tool"] == "test-linter"
        assert result["error_type"] == "missing_tool"
        assert "not found" in result["error"]
        assert result["installation_hint"] == "pip install test-linter"
        assert result["findings"] == []

    @patch("subprocess.run")
    def test_run_timeout(self, mock_run, tmp_role: Path):
        """Should return timeout error when execution times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=300)

        linter = ConcreteTestLinter()
        result = linter.run(str(tmp_role))

        assert result["tool"] == "test-linter"
        assert result["error_type"] == "timeout"
        assert "timeout" in result["error"].lower()
        assert result["findings"] == []

    @patch("subprocess.run")
    def test_run_success_no_findings(self, mock_run, tmp_role: Path):
        """Should return empty findings on success with clean code."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        linter = ConcreteTestLinter()
        result = linter.run(str(tmp_role))

        assert result["tool"] == "test-linter"
        assert result["role_path"] == str(tmp_role.resolve())
        assert result["findings"] == []
        assert result["summary"] == {"critical": 0, "warning": 0, "info": 0}
        assert "error" not in result

    @patch("subprocess.run")
    def test_run_success_with_findings(self, mock_run, tmp_role: Path):
        """Should return findings and summary on success."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="some output",
            stderr="",
        )

        linter = ConcreteTestLinter()
        linter.mock_findings = [
            {"file": "tasks/main.yml", "line": 1, "column": 1, "severity": "critical",
             "rule": "test-rule", "message": "Test error", "tool": "test-linter"},
            {"file": "tasks/main.yml", "line": 2, "column": 1, "severity": "warning",
             "rule": "test-rule", "message": "Test warning", "tool": "test-linter"},
        ]

        result = linter.run(str(tmp_role))

        assert result["tool"] == "test-linter"
        assert len(result["findings"]) == 2
        assert result["summary"] == {"critical": 1, "warning": 1, "info": 0}

    @patch("subprocess.run")
    def test_run_uses_timeout(self, mock_run, tmp_role: Path):
        """Should pass timeout to subprocess.run."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        linter = ConcreteTestLinter()
        linter.run(str(tmp_role))

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == TIMEOUT_SECONDS


class TestTimeoutConstant:
    """Tests for TIMEOUT_SECONDS constant."""

    def test_timeout_is_reasonable(self):
        """Timeout should be between 1 and 10 minutes."""
        assert 60 <= TIMEOUT_SECONDS <= 600
