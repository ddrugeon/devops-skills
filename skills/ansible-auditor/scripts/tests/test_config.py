"""Tests for config module."""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    AuditConfig,
    LinterConfig,
    load_config,
    DEFAULT_TIMEOUT_SECONDS,
    YAMLLINT_SEVERITY_MAP,
    ANSIBLE_LINT_SEVERITY_MAP,
    CHECKOV_SEVERITY_MAP,
)


class TestSeverityMaps:
    """Tests for severity mapping constants."""

    def test_yamllint_map_has_error(self):
        """Yamllint map should have error level."""
        assert "error" in YAMLLINT_SEVERITY_MAP
        assert YAMLLINT_SEVERITY_MAP["error"] == "critical"

    def test_ansible_lint_map_has_blocker(self):
        """Ansible-lint map should have blocker level."""
        assert "blocker" in ANSIBLE_LINT_SEVERITY_MAP
        assert ANSIBLE_LINT_SEVERITY_MAP["blocker"] == "critical"

    def test_checkov_map_has_high(self):
        """Checkov map should have HIGH level."""
        assert "HIGH" in CHECKOV_SEVERITY_MAP
        assert CHECKOV_SEVERITY_MAP["HIGH"] == "critical"


class TestLinterConfig:
    """Tests for LinterConfig dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = LinterConfig()
        assert config.enabled is True
        assert config.timeout == DEFAULT_TIMEOUT_SECONDS
        assert config.extra_args == []

    def test_custom_values(self):
        """Should accept custom values."""
        config = LinterConfig(
            enabled=False,
            timeout=60,
            extra_args=["--strict"],
        )
        assert config.enabled is False
        assert config.timeout == 60
        assert config.extra_args == ["--strict"]


class TestAuditConfig:
    """Tests for AuditConfig dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = AuditConfig()
        assert config.yamllint.enabled is True
        assert config.ansible_lint.enabled is True
        assert config.checkov.enabled is True
        assert config.parallel is False
        assert config.fail_on_error is False

    def test_from_dict_empty(self):
        """Should handle empty dict."""
        config = AuditConfig.from_dict({})
        assert config.yamllint.enabled is True

    def test_from_dict_partial(self):
        """Should handle partial configuration."""
        config = AuditConfig.from_dict({
            "yamllint": {"enabled": False},
            "fail_on_error": True,
        })
        assert config.yamllint.enabled is False
        assert config.ansible_lint.enabled is True  # Default
        assert config.fail_on_error is True

    def test_from_dict_full(self):
        """Should handle full configuration."""
        data = {
            "yamllint": {"enabled": True, "timeout": 60, "extra_args": ["-d", "relaxed"]},
            "ansible_lint": {"enabled": False, "timeout": 120, "extra_args": []},
            "checkov": {"enabled": True, "timeout": 180, "extra_args": ["--compact"]},
            "parallel": True,
            "fail_on_error": True,
        }
        config = AuditConfig.from_dict(data)

        assert config.yamllint.enabled is True
        assert config.yamllint.timeout == 60
        assert config.yamllint.extra_args == ["-d", "relaxed"]
        assert config.ansible_lint.enabled is False
        assert config.checkov.extra_args == ["--compact"]
        assert config.parallel is True
        assert config.fail_on_error is True

    def test_to_dict(self):
        """Should convert to dictionary."""
        config = AuditConfig()
        config.yamllint.enabled = False
        config.fail_on_error = True

        data = config.to_dict()

        assert data["yamllint"]["enabled"] is False
        assert data["ansible_lint"]["enabled"] is True
        assert data["fail_on_error"] is True

    def test_roundtrip(self):
        """from_dict and to_dict should be reversible."""
        original = {
            "yamllint": {"enabled": False, "timeout": 100, "extra_args": ["--arg"]},
            "ansible_lint": {"enabled": True, "timeout": 200, "extra_args": []},
            "checkov": {"enabled": True, "timeout": 300, "extra_args": []},
            "parallel": True,
            "fail_on_error": True,
        }
        config = AuditConfig.from_dict(original)
        result = config.to_dict()

        assert result == original


class TestLoadConfig:
    """Tests for load_config function."""

    def test_none_returns_default(self):
        """Should return default config for None path."""
        config = load_config(None)
        assert isinstance(config, AuditConfig)
        assert config.yamllint.enabled is True

    def test_nonexistent_path_returns_default(self, tmp_path: Path):
        """Should return default config for non-existent path."""
        config = load_config(tmp_path / "nonexistent.json")
        assert isinstance(config, AuditConfig)
        assert config.yamllint.enabled is True

    def test_load_json_file(self, tmp_path: Path):
        """Should load JSON configuration file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "yamllint": {"enabled": False},
            "fail_on_error": True,
        }))

        config = load_config(config_file)

        assert config.yamllint.enabled is False
        assert config.fail_on_error is True

    def test_load_empty_json_file(self, tmp_path: Path):
        """Should handle empty JSON file."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        config = load_config(config_file)
        assert config.yamllint.enabled is True  # Default


class TestDefaultTimeout:
    """Tests for DEFAULT_TIMEOUT_SECONDS constant."""

    def test_timeout_is_reasonable(self):
        """Timeout should be between 1 and 10 minutes."""
        assert 60 <= DEFAULT_TIMEOUT_SECONDS <= 600
