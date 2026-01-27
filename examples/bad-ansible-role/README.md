# Bad Role - Test Role for Ansible Auditor

This role intentionally violates Ansible best practices to test the ansible-auditor skill.

## Included Violations

### Security (SEC)

- [x] SEC1: Hardcoded secrets (passwords, API keys, SSH keys)
- [x] SEC2: Missing `no_log` for sensitive data
- [x] SEC3: Unnecessary privilege escalation
- [x] SEC4: Insecure file permissions (0777)
- [x] SEC5: Command injection vulnerability

### Genericity (G)

- [x] G1: Hardcoded values instead of variables
- [x] G2: Missing `default` filter for undefined variables
- [x] G4: Hardcoded absolute paths
- [x] G5: Hardcoded versions

### Reusability (R)

- [x] R2: Dependencies without version pinning
- [x] R3: Bad variable naming (no prefix, dashes, inconsistent case)
- [x] R4: Missing tags on tasks
- [x] R5: Handler naming issues

### Structure (S)

- [x] S3: Empty description in meta
- [x] S6: Non-optional variables without comments

### Modules (MOD)

- [x] MOD1: Missing FQCN
- [x] MOD2: Deprecated module (`include`)
- [x] MOD3: Using shell/command instead of dedicated modules
- [x] MOD6: Missing `changed_when`
- [x] MOD7: Unnecessary use of `raw` module

### Tasks (T)

- [x] T1: Missing task names
- [x] T2: Non-idempotent tasks
- [x] T4: Unjustified `ignore_errors`
- [x] T6: Templates without `ansible_managed`
- [x] T7: Inefficient loops
- [x] T8: Complex conditionals
- [x] T11: Debug without verbosity
- [x] T12: Dot notation for facts

### YAML Syntax

- [x] Inconsistent indentation
- [x] Trailing spaces (potential)

## Usage

Run the auditor on this role to test detection:

```bash
python scripts/run_all.py test/bad-role
```
