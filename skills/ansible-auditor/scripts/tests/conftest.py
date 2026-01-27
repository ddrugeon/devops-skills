"""Pytest fixtures for linter tests."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_role(tmp_path: Path) -> Path:
    """Create a minimal Ansible role structure for testing."""
    role_path = tmp_path / "test-role"
    role_path.mkdir()

    # Create basic structure
    (role_path / "tasks").mkdir()
    (role_path / "defaults").mkdir()
    (role_path / "meta").mkdir()

    # Create main.yml files
    (role_path / "tasks" / "main.yml").write_text(
        """---
- name: Test task
  ansible.builtin.debug:
    msg: "Hello World"
"""
    )

    (role_path / "defaults" / "main.yml").write_text(
        """---
test_role_variable: "default_value"
"""
    )

    (role_path / "meta" / "main.yml").write_text(
        """---
galaxy_info:
  author: test
  description: Test role
  license: MIT
  min_ansible_version: "2.9"
"""
    )

    return role_path


@pytest.fixture
def tmp_role_with_errors(tmp_path: Path) -> Path:
    """Create an Ansible role with intentional errors for testing."""
    role_path = tmp_path / "bad-role"
    role_path.mkdir()

    (role_path / "tasks").mkdir()

    # Create a file with YAML syntax errors
    (role_path / "tasks" / "main.yml").write_text(
        """---
- name: Bad indentation
  debug:
    msg: "test"
   invalid_key: value
- name: Missing quotes
  debug:
    msg: {{ variable }}
"""
    )

    return role_path


@pytest.fixture
def nonexistent_path(tmp_path: Path) -> Path:
    """Return a path that does not exist."""
    return tmp_path / "nonexistent-role"
