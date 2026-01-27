# Examples

This directory contains example Ansible roles for testing and demonstration purposes.

## bad-ansible-role

A deliberately flawed Ansible role designed to test the `ansible-auditor` skill. This role demonstrates common anti-patterns and violations of Ansible best practices.

### Purpose

Use this role to:

- Test the ansible-auditor skill detection capabilities
- Learn what NOT to do when writing Ansible roles
- Understand the impact of security and quality violations

### Running the Audit

```bash
# Using the ansible-auditor skill
/audit ansible role ./bad-ansible-role/

# Or using the linter scripts directly
python3 scripts/run_all.py ./bad-ansible-role/
```

---

## Audit Report: bad-ansible-role

**Date**: 2026-01-27

### Summary

| Severity | Count |
|----------|-------|
| Critical | 14 |
| Warning | 55 |
| Info | 8 |

---

### Security Issues (SEC)

| Severity | Location | Rule | Issue |
|----------|----------|------|-------|
| Critical | `files/credentials.txt` | SEC1 | Plain-text credentials file with AWS keys, database URL, and API tokens |
| Critical | `defaults/main.yml:9-10` | SEC1 | Hardcoded `db_password` and `api_secret_key` |
| Critical | `vars/main.yml:5-9` | SEC1 | Hardcoded `mysql_root_password` and SSH private key |
| Critical | `templates/app.conf.j2:10` | SEC1 | Hardcoded database password in template |
| Critical | `tasks/main.yml:26` | SEC1 | Hardcoded MySQL password in task |
| Critical | `tasks/main.yml:31-32` | SEC2 | `set_fact` with API token missing `no_log: true` |
| Critical | `tasks/main.yml:67` | SEC5 | Command injection vulnerability: `echo {{ user_input }}` |
| Critical | `tasks/main.yml:105` | SEC4 | Insecure file permissions `mode: 0777` on secret file |
| Warning | `tasks/main.yml:123-125` | SEC3 | Unnecessary `become: yes` for reading public file |

**Recommendations:**

- Remove `files/credentials.txt` immediately
- Use Ansible Vault or external secret managers for all credentials
- Add `no_log: true` to tasks handling sensitive data
- Use `{{ variable | quote }}` filter and input validation for shell commands
- Use `mode: '0600'` for files containing secrets

---

### Genericity Issues (G)

| Severity | Location | Rule | Issue |
|----------|----------|------|-------|
| Critical | `templates/app.conf.j2:6` | G1 | Hardcoded IP address `192.168.1.100` |
| Warning | `defaults/main.yml:13-14` | G3 | Hardcoded OS-specific values (`package_manager: apt`) |
| Warning | `tasks/main.yml:53, 62` | G4 | Hardcoded absolute paths |
| Warning | `vars/main.yml:15-17` | G4 | Hardcoded paths in vars |
| Warning | `defaults/main.yml:23-24` | G5 | Fixed versions without override capability |
| Warning | `tasks/main.yml:92` | G2 | Variable used without `default` filter |
| Warning | `templates/app.conf.j2:13-14` | G2 | Template variables without `default` or `mandatory` filter |

**Recommendations:**

- Replace hardcoded values with variables
- Use `ansible.builtin.package` or OS conditionals instead of hardcoded package managers
- Provide default values with override capability: `{{ var | default('value') }}`

---

### Reusability Issues (R)

| Severity | Location | Rule | Issue |
|----------|----------|------|-------|
| Critical | `meta/main.yml:21-24` | R2 | Dependencies without version pinning |
| Warning | Role name | R7 | Role name `bad-ansible-role` contains dashes |
| Warning | `defaults/main.yml:5-6` | R3 | Variables not prefixed with role name |
| Warning | `defaults/main.yml:20` | R3 | Dashes in variable name (`my-variable-with-dashes`) |
| Warning | `vars/main.yml:12` | R3 | Internal variable without `__` prefix |
| Warning | `handlers/main.yml:5` | R5 | Handler names lowercase and missing `listen` directive |
| Info | `tasks/main.yml` | R4 | Tasks missing role-prefixed tags |

**Recommendations:**

- Rename role to `bad_ansible_role` (underscores only)
- Prefix all variables with role name: `bad_ansible_role_app_port`
- Pin dependency versions: `{ role: geerlingguy.docker, version: "6.1.0" }`
- Use `__` prefix for internal variables

---

### Structure Issues (S)

| Severity | Location | Rule | Issue |
|----------|----------|------|-------|
| Warning | `meta/main.yml:6` | S3 | Empty description |
| Warning | `meta/main.yml:9` | S3 | `min_ansible_version: 2.1` is very outdated |
| Warning | `meta/main.yml:14` | S3 | Platform Ubuntu 16.04 is EOL |
| Info | Role | S5 | `community.mysql` collection used but not declared |
| Info | Role | S7 | Missing `meta/argument_specs.yml` |
| Warning | Role | S1 | No `molecule/` directory for tests |

**Recommendations:**

- Add meaningful role description
- Update `min_ansible_version` to at least `"2.14"`
- Update platforms to supported versions (22.04, 24.04)
- Declare collections in `meta/main.yml`
- Create `meta/argument_specs.yml` for parameter validation
- Add Molecule tests

---

### Module Usage Issues (MOD)

| Severity | Location | Rule | Issue |
|----------|----------|------|-------|
| Warning | `tasks/main.yml:5, 10, 31, 51, 60, 81` | MOD1 | Modules used without FQCN |
| Warning | `tasks/main.yml:15` | MOD3 | `shell: apt-get install` instead of `apt` module |
| Warning | `tasks/main.yml:20` | MOD3 | `command: mkdir -p` instead of `file` module |
| Warning | `tasks/main.yml:77` | MOD7 | Unnecessary use of `raw` module |
| Warning | `tasks/main.yml:114` | MOD2 | Deprecated `include` module |
| Warning | Multiple locations | MOD6 | Commands missing `changed_when` |

**Recommendations:**

- Use FQCN for all modules: `ansible.builtin.debug`, `ansible.builtin.copy`, etc.
- Replace shell commands with dedicated modules
- Replace `include` with `ansible.builtin.include_tasks`
- Add `changed_when: false` to read-only commands

---

### Task Best Practices Issues (T)

| Severity | Location | Rule | Issue |
|----------|----------|------|-------|
| Warning | `tasks/main.yml:5` | T1 | Missing task name |
| Warning | `tasks/other_tasks.yml:14` | T1 | Unnamed shell task |
| Warning | `tasks/main.yml:36` | T2 | Non-idempotent task (runs every time) |
| Warning | `tasks/main.yml:46` | T4 | `ignore_errors: yes` without justification |
| Warning | Templates | T6 | Missing `{{ ansible_managed \| comment }}` header |
| Info | `tasks/main.yml:80-87` | T7 | Inefficient loop (users created one-by-one) |
| Info | `tasks/main.yml:98` | T8 | Complex multi-line `when` clause |
| Info | `tasks/main.yml:118-120` | T11 | Debug without `verbosity` parameter |
| Info | `tasks/main.yml:130` | T12 | Dot notation for facts instead of bracket notation |

**Recommendations:**

- Always name tasks with descriptive, action-oriented names
- Add `creates:` parameter or use idempotent modules
- Use `failed_when` instead of `ignore_errors`
- Add `{{ ansible_managed | comment }}` to all templates
- Use `ansible_facts['os_family']` instead of `ansible_facts.os_family`

---

### YAML Syntax Issues

| Severity | Location | Issue |
|----------|----------|-------|
| Critical | `meta/main.yml:24` | Too many spaces inside braces |
| Critical | `tasks/main.yml:98` | Line too long (216 > 80 characters) |
| Warning | `tasks/main.yml:16, 42, 47, 125` | Truthy values `yes`/`no` instead of `true`/`false` |
| Warning | `tasks/main.yml:56, 63, 105` | Implicit octal values (should be quoted strings) |

**Recommendations:**

- Use `true`/`false` instead of `yes`/`no`
- Quote file modes: `mode: '0644'`
- Keep lines under 80-120 characters

---

### Priority Remediation Checklist

1. **CRITICAL** - Remove `files/credentials.txt` and all hardcoded secrets
2. **CRITICAL** - Fix command injection at `tasks/main.yml:67`
3. **CRITICAL** - Fix file permissions `0777` to `0600` for secrets
4. **CRITICAL** - Add `no_log: true` to sensitive tasks
5. **HIGH** - Use FQCN for all modules (`ansible.builtin.*`)
6. **HIGH** - Replace deprecated `include` with `include_tasks`
7. **HIGH** - Add `changed_when` to command/shell tasks
8. **HIGH** - Rename role to use underscores only
9. **MEDIUM** - Prefix all variables with role name
10. **MEDIUM** - Pin dependency versions and update `min_ansible_version`

---

### Files Structure

```text
bad-ansible-role/
├── README.md              # Role documentation (violations list)
├── defaults/
│   └── main.yml           # Default variables (with bad practices)
├── files/
│   └── credentials.txt    # CRITICAL: Plain-text credentials (should not exist)
├── handlers/
│   └── main.yml           # Handlers (with naming issues)
├── meta/
│   └── main.yml           # Role metadata (incomplete)
├── tasks/
│   ├── main.yml           # Main tasks (multiple violations)
│   └── other_tasks.yml    # Additional tasks (more violations)
├── templates/
│   ├── app.conf.j2        # Template (missing ansible_managed, hardcoded values)
│   └── unmanaged.conf.j2  # Template (missing ansible_managed)
└── vars/
    └── main.yml           # Variables (secrets in plain text)
```

---

### References

- [Red Hat Automation Good Practices](https://redhat-cop.github.io/automation-good-practices/)
- [Ansible Documentation](https://docs.ansible.com/ansible/latest/)
- [Ansible Lint Rules](https://ansible.readthedocs.io/projects/lint/rules/)
- [Ansible Collections Index](https://docs.ansible.com/ansible/latest/collections/index.html)
