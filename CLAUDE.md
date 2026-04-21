# CLAUDE.md — devops-skills

## Project overview

Collection of Claude Code skills for DevOps/SRE work, following the
[Agent Skills](https://agentskills.io) standard. Compatible with Claude Code
and OpenCode.

Plugin: `ddrugeon/devops-skills` (v0.1.0, MIT)

## Repository structure

```text
skills/
  <skill-name>/
    SKILL.md              # Skill definition (frontmatter: name, description, version, tags)
    references/*.md       # Reference docs loaded on-demand by the skill
    scripts/*.py          # Automation scripts (ansible-auditor only)
.claude-plugin/
  plugin.json             # Claude Code plugin manifest
  marketplace.json        # Marketplace listing
.github/workflows/
  validate.yml            # CI: YAML, JSON, Markdown, link validation
examples/
  bad-ansible-role/       # Example Ansible role for testing ansible-auditor
```

## Available skills

| Skill | Version | Description |
|-------|---------|-------------|
| `ansible-auditor` | 0.1.0 | Audits Ansible roles against 59 Red Hat Good Practices rules using yamllint, ansible-lint, checkov |
| `zabbix-template-generator` | 0.1.0 | Generates Zabbix 7.0 YAML templates from Prometheus `/metrics` endpoints |
| `zabbix-runbook-generator` | 0.1.0 | Generates a complete French operational runbook (Markdown) from a `zbx_template_*.yaml` file |

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md` with required frontmatter:

```yaml
---
name: skill-name
description: |
  Detailed description including trigger phrases.
version: 0.1.0
author: ddrugeon
tags: ["tag1", "tag2"]
---
```

1. Add reference files in `skills/<skill-name>/references/` if needed
1. Add the skill to the table in `README.md`
1. Add an entry in `.claude-plugin/plugin.json` under the `skills[]` array
1. If scripts are needed, place them in `skills/<skill-name>/scripts/`

All skill content (SKILL.md, references) must be written in **English**.

## ansible-auditor scripts

Located at `skills/ansible-auditor/scripts/`. Python venv at `scripts/.venv/`.

```bash
# Run all linters on a role
python skills/ansible-auditor/scripts/run_all.py <role_path>

# Run individual linters
python skills/ansible-auditor/scripts/run_yamllint.py <role_path>
python skills/ansible-auditor/scripts/run_ansiblelint.py <role_path>
python skills/ansible-auditor/scripts/run_checkov.py <role_path>
```

Options: `--no-yamllint`, `--no-ansible-lint`, `--no-checkov`, `--config <file>`, `--fail-on-error`

## Quality checks

### Pre-commit hooks (local)

```bash
pre-commit install   # Install hooks
prek run             # Run checks (token-optimized proxy for pre-commit)
```

Hooks: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `markdownlint`

### CI (GitHub Actions)

`.github/workflows/validate.yml` runs on push/PR to `main`:

- YAML validation via `yamllint -d relaxed`
- JSON validation of `.claude-plugin/plugin.json` and `marketplace.json`
- Markdown linting via `markdownlint-cli`
- Link checking via `markdown-link-check` with `.markdown-link-check.json` config

### Markdownlint config

`.markdownlint.json` — applied to all `*.md` files.

## Key constraints

- SKILL.md frontmatter is mandatory and must be valid YAML
- UUIDs in Zabbix templates must be 32-char hex without dashes:
  `python3 -c "import uuid; print(uuid.uuid4().hex)"`
- Do not commit `skills/ansible-auditor/scripts/.venv/` (already gitignored)
