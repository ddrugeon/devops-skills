"""Tests for run_all module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import AuditConfig
from run_all import (
    aggregate_summaries,
    run_all_linters,
    AggregatedResult,
    AggregatedSummary,
)


class TestAggregateSummaries:
    """Tests for aggregate_summaries function."""

    def test_empty_results(self):
        """Should handle empty results."""
        result = aggregate_summaries({})

        assert result["total_findings"] == 0
        assert result["critical"] == 0
        assert result["warning"] == 0
        assert result["info"] == 0
        assert result["linters_run"] == 0
        assert result["linters_failed"] == 0

    def test_single_linter_no_findings(self):
        """Should handle single linter with no findings."""
        results = {
            "yamllint": {
                "tool": "yamllint",
                "findings": [],
                "summary": {"critical": 0, "warning": 0, "info": 0},
            }
        }
        result = aggregate_summaries(results)

        assert result["total_findings"] == 0
        assert result["linters_run"] == 1
        assert result["linters_failed"] == 0

    def test_single_linter_with_findings(self):
        """Should count findings from single linter."""
        results = {
            "yamllint": {
                "tool": "yamllint",
                "findings": [{"severity": "critical"}],
                "summary": {"critical": 2, "warning": 3, "info": 1},
            }
        }
        result = aggregate_summaries(results)

        assert result["total_findings"] == 6
        assert result["critical"] == 2
        assert result["warning"] == 3
        assert result["info"] == 1

    def test_multiple_linters(self):
        """Should aggregate findings from multiple linters."""
        results = {
            "yamllint": {
                "tool": "yamllint",
                "findings": [],
                "summary": {"critical": 1, "warning": 2, "info": 0},
            },
            "ansible-lint": {
                "tool": "ansible-lint",
                "findings": [],
                "summary": {"critical": 3, "warning": 1, "info": 5},
            },
            "checkov": {
                "tool": "checkov",
                "findings": [],
                "summary": {"critical": 0, "warning": 4, "info": 2},
            },
        }
        result = aggregate_summaries(results)

        assert result["total_findings"] == 18
        assert result["critical"] == 4  # 1 + 3 + 0
        assert result["warning"] == 7  # 2 + 1 + 4
        assert result["info"] == 7  # 0 + 5 + 2
        assert result["linters_run"] == 3
        assert result["linters_failed"] == 0

    def test_linter_with_error(self):
        """Should count failed linters."""
        results = {
            "yamllint": {
                "tool": "yamllint",
                "error": "yamllint not found",
                "error_type": "missing_tool",
                "findings": [],
            },
            "ansible-lint": {
                "tool": "ansible-lint",
                "findings": [],
                "summary": {"critical": 1, "warning": 0, "info": 0},
            },
        }
        result = aggregate_summaries(results)

        assert result["total_findings"] == 1
        assert result["linters_run"] == 2
        assert result["linters_failed"] == 1

    def test_all_linters_failed(self):
        """Should handle all linters failing."""
        results = {
            "yamllint": {
                "tool": "yamllint",
                "error": "not found",
                "findings": [],
            },
            "ansible-lint": {
                "tool": "ansible-lint",
                "error": "not found",
                "findings": [],
            },
        }
        result = aggregate_summaries(results)

        assert result["total_findings"] == 0
        assert result["linters_run"] == 2
        assert result["linters_failed"] == 2


class TestRunAllLinters:
    """Tests for run_all_linters function."""

    @patch("run_all.run_yamllint")
    @patch("run_all.run_ansible_lint")
    @patch("run_all.run_checkov")
    def test_runs_all_enabled_linters(
        self, mock_checkov, mock_ansible, mock_yaml, tmp_role: Path
    ):
        """Should run all enabled linters."""
        mock_yaml.return_value = {
            "tool": "yamllint",
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 0},
        }
        mock_ansible.return_value = {
            "tool": "ansible-lint",
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 0},
        }
        mock_checkov.return_value = {
            "tool": "checkov",
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 0},
        }

        result = run_all_linters(str(tmp_role))

        mock_yaml.assert_called_once()
        mock_ansible.assert_called_once()
        mock_checkov.assert_called_once()
        assert "yamllint" in result["linters"]
        assert "ansible-lint" in result["linters"]
        assert "checkov" in result["linters"]

    @patch("run_all.run_yamllint")
    @patch("run_all.run_ansible_lint")
    @patch("run_all.run_checkov")
    def test_respects_disabled_linters(
        self, mock_checkov, mock_ansible, mock_yaml, tmp_role: Path
    ):
        """Should not run disabled linters."""
        config = AuditConfig()
        config.yamllint.enabled = False
        config.checkov.enabled = False

        mock_ansible.return_value = {
            "tool": "ansible-lint",
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 0},
        }

        result = run_all_linters(str(tmp_role), config)

        mock_yaml.assert_not_called()
        mock_checkov.assert_not_called()
        mock_ansible.assert_called_once()
        assert "yamllint" not in result["linters"]
        assert "ansible-lint" in result["linters"]
        assert "checkov" not in result["linters"]

    @patch("run_all.run_yamllint")
    @patch("run_all.run_ansible_lint")
    @patch("run_all.run_checkov")
    def test_returns_correct_structure(
        self, mock_checkov, mock_ansible, mock_yaml, tmp_role: Path
    ):
        """Should return correctly structured result."""
        for mock in [mock_yaml, mock_ansible, mock_checkov]:
            mock.return_value = {
                "tool": "test",
                "findings": [],
                "summary": {"critical": 0, "warning": 0, "info": 0},
            }

        result = run_all_linters(str(tmp_role))

        assert "role_path" in result
        assert "timestamp" in result
        assert "linters" in result
        assert "summary" in result
        assert result["role_path"] == str(tmp_role.resolve())

    @patch("run_all.run_yamllint")
    @patch("run_all.run_ansible_lint")
    @patch("run_all.run_checkov")
    def test_aggregates_findings(
        self, mock_checkov, mock_ansible, mock_yaml, tmp_role: Path
    ):
        """Should aggregate findings from all linters."""
        mock_yaml.return_value = {
            "tool": "yamllint",
            "findings": [{"severity": "critical"}],
            "summary": {"critical": 1, "warning": 0, "info": 0},
        }
        mock_ansible.return_value = {
            "tool": "ansible-lint",
            "findings": [{"severity": "warning"}],
            "summary": {"critical": 0, "warning": 2, "info": 0},
        }
        mock_checkov.return_value = {
            "tool": "checkov",
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 3},
        }

        result = run_all_linters(str(tmp_role))

        assert result["summary"]["total_findings"] == 6
        assert result["summary"]["critical"] == 1
        assert result["summary"]["warning"] == 2
        assert result["summary"]["info"] == 3

    @patch("run_all.run_yamllint")
    @patch("run_all.run_ansible_lint")
    @patch("run_all.run_checkov")
    def test_handles_linter_errors(
        self, mock_checkov, mock_ansible, mock_yaml, tmp_role: Path
    ):
        """Should handle linter errors gracefully."""
        mock_yaml.return_value = {
            "tool": "yamllint",
            "error": "not found",
            "error_type": "missing_tool",
            "findings": [],
        }
        mock_ansible.return_value = {
            "tool": "ansible-lint",
            "findings": [],
            "summary": {"critical": 1, "warning": 0, "info": 0},
        }
        mock_checkov.return_value = {
            "tool": "checkov",
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 0},
        }

        result = run_all_linters(str(tmp_role))

        assert result["summary"]["linters_failed"] == 1
        assert result["summary"]["linters_run"] == 3
        assert "error" in result["linters"]["yamllint"]

    @patch("run_all.run_yamllint")
    @patch("run_all.run_ansible_lint")
    @patch("run_all.run_checkov")
    def test_uses_default_config_when_none(
        self, mock_checkov, mock_ansible, mock_yaml, tmp_role: Path
    ):
        """Should use default config when None is provided."""
        for mock in [mock_yaml, mock_ansible, mock_checkov]:
            mock.return_value = {
                "tool": "test",
                "findings": [],
                "summary": {"critical": 0, "warning": 0, "info": 0},
            }

        result = run_all_linters(str(tmp_role), None)

        # All linters should be called with default config
        mock_yaml.assert_called_once()
        mock_ansible.assert_called_once()
        mock_checkov.assert_called_once()
