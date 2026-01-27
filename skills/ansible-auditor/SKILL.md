---
name: ansible-auditor
description: |
  Comprehensive Ansible role auditor based on Red Hat Automation Good Practices.
  Performs in-depth analysis across 59 rules covering security, structure, modules,
  tasks, genericity, reusability, and Molecule tests.
  Use when the user asks to: audit an Ansible role, check Ansible best practices,
  analyze role quality, detect security vulnerabilities, validate a role,
  "audit ansible", "lint ansible", "review ansible role", "check role quality".
  Combines automated linting (yamllint, ansible-lint, checkov) with manual analysis
  against Red Hat Community of Practice guidelines.
version: 0.1.0
author: ddrugeon
tags: ["ansible", "audit", "security", "best-practices", "redhat"]
---

# Ansible Role Auditor

Audits an Ansible role and generates a structured report by category with severity levels and suggestions.

## Workflow

### 1. Run the linters

Execute the unified linter script on the role path:

```bash
python scripts/run_all.py <role_path>
```

The script returns aggregated JSON with all linter results:

```json
{
  "role_path": "/path/to/role",
  "timestamp": "2024-01-15T10:30:00+00:00",
  "linters": {
    "yamllint": {
      "tool": "yamllint",
      "findings": [{"file", "line", "column", "severity", "rule", "message"}],
      "summary": {"critical": N, "warning": N, "info": N}
    },
    "ansible-lint": { ... },
    "checkov": { ... }
  },
  "summary": {
    "total_findings": N,
    "critical": N,
    "warning": N,
    "info": N,
    "linters_run": 3,
    "linters_failed": 0
  }
}
```

**Options:**

- `--no-yamllint`, `--no-ansible-lint`, `--no-checkov`: Disable specific linters
- `--config <file>`: Use a JSON/YAML configuration file
- `--fail-on-error`: Exit with code 1 if findings are detected

**Alternative:** Run linters individually if needed:

```bash
python scripts/run_yamllint.py <role_path>
python scripts/run_ansiblelint.py <role_path>
python scripts/run_checkov.py <role_path>
```

### 2. Analyze genericity, reusability, structure and tests

Load the relevant reference files based on context:

| File | When to load |
|------|--------------|
| `references/genericity.md` | Always - rules G1-G6 |
| `references/reusability.md` | Always - rules R1-R7 |
| `references/structure.md` | Always - rules S1-S7 |
| `references/security.md` | Always - rules SEC1-SEC10 |
| `references/modules.md` | Always - rules MOD1-MOD7 |
| `references/tasks.md` | Always - rules T1-T12 |
| `references/molecule.md` | If `molecule/` is present or if full audit requested - rules M1-M10 |

Manually evaluate each applicable rule.

### 3. Generate the report

Use the template below. Group by category, order by decreasing severity.

## Report Template

```markdown
# Ansible Audit Report: {role_name}

**Date**: {date}
**Path**: {role_path}

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | {n} |
| 🟠 Warning | {n} |
| 🟡 Info | {n} |

## Issues by Category

### YAML Syntax
<!-- yamllint issues -->

| Severity | File | Line | Issue | Suggestion |
|----------|------|------|-------|------------|
| ... | ... | ... | ... | ... |

### Ansible Best Practices
<!-- ansible-lint issues -->

| Severity | File | Line | Rule | Issue | Suggestion |
|----------|------|------|------|-------|------------|
| ... | ... | ... | ... | ... | ... |

### Security (Automated)
<!-- checkov issues -->

| Severity | File | Line | Rule | Issue | Suggestion |
|----------|------|------|------|-------|------------|
| ... | ... | ... | ... | ... | ... |

### Security (Manual)
<!-- Manual analysis according to references/security.md -->

| Severity | File | Rule | Issue | Suggestion |
|----------|------|------|-------|------------|
| ... | ... | ... | ... | ... |

### Genericity
<!-- Manual analysis according to references/genericity.md -->

| Severity | File | Issue | Suggestion |
|----------|------|-------|------------|
| ... | ... | ... | ... |

### Reusability
<!-- Manual analysis according to references/reusability.md -->

| Severity | File | Issue | Suggestion |
|----------|------|-------|------------|
| ... | ... | ... | ... |

### Role Structure
<!-- Manual analysis according to references/structure.md -->

| Severity | Element | Issue | Suggestion |
|----------|---------|-------|------------|
| ... | ... | ... | ... |

### Module Usage
<!-- Manual analysis according to references/modules.md -->

| Severity | File | Line | Rule | Issue | Suggestion |
|----------|------|------|------|-------|------------|
| ... | ... | ... | ... | ... | ... |

### Task Best Practices
<!-- Manual analysis according to references/tasks.md -->

| Severity | File | Line | Rule | Issue | Suggestion |
|----------|------|------|------|-------|------------|
| ... | ... | ... | ... | ... | ... |

### Molecule Tests
<!-- Manual analysis according to references/molecule.md -->

| Severity | Element | Issue | Suggestion |
|----------|---------|-------|------------|
| ... | ... | ... | ... |

## Priority Recommendations

1. {Critical recommendation 1}
2. {Critical recommendation 2}
3. ...
```

## Severity Levels

- 🔴 **Critical**: Security, blocking errors, broken dependencies
- 🟠 **Warning**: Bad practices impacting maintainability
- 🟡 **Info**: Recommended improvements, conventions

## Notes

- If a linter is not installed, the script returns an error with `error_type: "missing_tool"` and an `installation_hint` field - indicate this in the report and continue with the others
- The script handles timeouts (300s default) and returns `error_type: "timeout"` if exceeded
- Omit categories with no detected issues
- Suggestions should be actionable with code examples when relevant

## References

- [Red Hat Automation Good Practices](https://redhat-cop.github.io/automation-good-practices/) - Official Red Hat Community of Practice guidelines
- [Ansible Documentation](https://docs.ansible.com/ansible/latest/)
- [Ansible Lint Rules](https://ansible.readthedocs.io/projects/lint/rules/)
- [Ansible Collections Index](https://docs.ansible.com/ansible/latest/collections/index.html)
