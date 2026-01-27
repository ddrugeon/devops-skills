# Genericity Rules

Evaluate the role's ability to work in different contexts.

## G1: Hardcoded Values (Critical)

Hardcoded values that should be variables.

```yaml
# ❌ Bad
- name: Create user
  user:
    name: deploy
    uid: 1001

# ✅ Good
- name: Create user
  user:
    name: "{{ app_user }}"
    uid: "{{ app_user_uid }}"
```

**Check for**: IPs, ports, absolute paths, usernames, fixed package versions.

## G2: Variables Without Defaults (Warning)

Variables used without a default value in `defaults/main.yml`.

```yaml
# defaults/main.yml - all variables should have a default value
app_user: deploy
app_port: 8080
app_install_path: /opt/app
```

## G3: Hardcoded OS/Distribution (Critical)

OS-specific logic without conditionals or platform-specific variable files.

```yaml
# ❌ Bad
- name: Install package
  ansible.builtin.apt:
    name: nginx

# ✅ Good - generic module
- name: Install package
  ansible.builtin.package:
    name: nginx
    state: present

# ✅ Good - explicit conditionals
- name: Install on Debian
  ansible.builtin.apt:
    name: nginx
  when: ansible_facts['os_family'] == "Debian"

- name: Install on RedHat
  ansible.builtin.dnf:
    name: nginx
  when: ansible_facts['os_family'] == "RedHat"
```

**Platform-specific variables** (Red Hat recommendation):

Use `first_found` lookup to load variables from most specific to least specific:

```yaml
# vars/ directory structure
vars/
├── RedHat.yml           # OS family defaults
├── Fedora.yml           # Distribution specific
├── RedHat_8.yml         # Distribution + major version
├── RedHat_8.3.yml       # Distribution + exact version
├── Debian.yml
├── Ubuntu.yml
└── Ubuntu_22.yml

# tasks/main.yml - Load platform-specific variables
- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ lookup('first_found', params) }}"
  vars:
    params:
      files:
        - "{{ ansible_facts['distribution'] }}_{{ ansible_facts['distribution_version'] }}.yml"
        - "{{ ansible_facts['distribution'] }}_{{ ansible_facts['distribution_major_version'] }}.yml"
        - "{{ ansible_facts['distribution'] }}.yml"
        - "{{ ansible_facts['os_family'] }}.yml"
        - default.yml
      paths:
        - "{{ role_path }}/vars"
```

**Handle gather_facts: false**:

```yaml
# Ensure minimal facts are gathered when needed
- name: Gather minimal facts if not available
  ansible.builtin.setup:
    gather_subset:
      - min
      - distribution
  when: ansible_facts['os_family'] is not defined
```

## G4: Non-Configurable Absolute Paths (Warning)

Absolute paths without variables.

```yaml
# ❌ Bad
- ansible.builtin.copy:
    dest: /etc/nginx/nginx.conf

# ✅ Good
- ansible.builtin.copy:
    dest: "{{ nginx_conf_path | default('/etc/nginx/nginx.conf') }}"
```

## G5: Fixed Versions Without Override (Warning)

Package versions without override capability.

```yaml
# ❌ Bad
- ansible.builtin.apt:
    name: nginx=1.18.0-1

# ✅ Good
- ansible.builtin.apt:
    name: "nginx={{ nginx_version | default('1.18.0-1') }}"
```

## G6: Missing Default or Required Filters (Warning)

Variables used without proper handling for optional/mandatory status.

**Use `default` filter for optional variables**:

```yaml
# ❌ Bad - fails if variable is undefined
- name: Set API endpoint
  ansible.builtin.set_fact:
    api_endpoint: "{{ custom_api_endpoint }}"

# ✅ Good - graceful fallback for optional variable
- name: Set API endpoint
  ansible.builtin.set_fact:
    api_endpoint: "{{ custom_api_endpoint | default('https://api.example.com') }}"

# ✅ Good - with omit for optional module parameters
- name: Create user
  ansible.builtin.user:
    name: "{{ app_user }}"
    shell: "{{ app_user_shell | default(omit) }}"
    groups: "{{ app_user_groups | default(omit) }}"
```

**Use `mandatory` filter for required variables**:

```yaml
# ❌ Bad - unclear error if variable is missing
- name: Configure database
  ansible.builtin.template:
    src: db.conf.j2
    dest: /etc/app/database.conf
  vars:
    db_password: "{{ database_password }}"

# ✅ Good - explicit requirement with clear error message
- name: Configure database
  ansible.builtin.template:
    src: db.conf.j2
    dest: /etc/app/database.conf
  vars:
    db_password: "{{ database_password | mandatory }}"

# ✅ Better - with ansible.builtin.assert for validation
- name: Validate required variables
  ansible.builtin.assert:
    that:
      - database_password is defined
      - database_password | length > 0
    fail_msg: "database_password must be defined and non-empty"
```

**Check for**:

- Variables used without `default` filter that could be undefined
- Critical variables (passwords, API keys) without explicit validation
- Module parameters that fail silently when variable is undefined
