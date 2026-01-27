# Reusability Rules

Evaluate how easily the role can be reused in different projects.

## R1: Monolithic Role (Warning)

Role that does too many things, difficult to partially reuse.

**Indicators**:

- `tasks/main.yml` > 100 lines
- More than 5 distinct responsibilities (install, configure, deploy, monitor, backup...)
- Cannot use one part without the rest

**Solutions**:

- Split into sub-roles
- Use tags for selective execution
- Separate into conditionally included files

```yaml
# tasks/main.yml - use conditional includes
- name: Include install tasks
  ansible.builtin.include_tasks: install.yml
  tags: [install]

- name: Include configure tasks
  ansible.builtin.include_tasks: configure.yml
  tags: [configure]
```

## R2: Implicit Dependencies (Critical)

The role assumes other roles have been executed without declaring them.

```yaml
# ❌ Bad - assumes Java is installed
- name: Start app
  ansible.builtin.command: java -jar app.jar

# ✅ Good - explicit dependency in meta/main.yml
# meta/main.yml
dependencies:
  - role: java
    vars:
      java_version: "11"
```

## R3: Poor Variable Naming (Warning)

Variable names that are too generic, unclear, or risk collisions with other roles.

**Naming conventions**:

- Prefix all variables with the role name to avoid collisions
- Use descriptive, self-documenting names
- Use snake_case consistently
- Group related variables with common prefixes

```yaml
# ❌ Bad - Generic, collision-prone, unclear
version: "1.18.0"       # Too generic - version of what?
workers: 4              # Unclear - workers for what?
db: "db.example.com"    # Vague abbreviation
port: 8080              # Which port? Conflicts with other roles
user: deploy            # Generic name
path: /opt/app          # Unclear purpose
config: {}              # Too generic

# ✅ Good - Descriptive, namespaced, self-documenting
nginx_version: "1.18.0"
nginx_worker_processes: 4
nginx_worker_connections: 1024

app_database_host: "db.example.com"
app_database_port: 5432
app_database_name: "myapp"

myapp_listen_port: 8080
myapp_service_user: deploy
myapp_install_path: /opt/app
myapp_config: {}
```

**Check for**:

- Variables without role prefix
- Single-word variable names (e.g., `port`, `user`, `config`)
- Abbreviations that are not self-explanatory
- Variables that could conflict with Ansible built-ins or other roles

**Internal variables convention** (Red Hat recommendation):

```yaml
# Use double underscore prefix for internal/private variables
__myapp_internal_state: "configured"
__myapp_computed_value: "{{ myapp_base_path }}/data"

# Public variables (user-configurable) - no underscore
myapp_port: 8080
myapp_user: appuser
```

## R4: Missing or Poorly Named Tags (Info)

No tags for selective execution, or tags without role prefix.

```yaml
# ❌ Bad - generic tags without prefix
- name: Install packages
  ansible.builtin.package:
    name: "{{ item }}"
  loop: "{{ packages }}"
  tags:
    - install
    - packages

# ✅ Good - tags prefixed with role name
- name: Install packages
  ansible.builtin.package:
    name: "{{ item }}"
  loop: "{{ nginx_packages }}"
  tags:
    - nginx
    - nginx_install
    - nginx_packages

- name: Configure service
  ansible.builtin.template:
    src: config.j2
    dest: "{{ nginx_config_path }}"
  tags:
    - nginx
    - nginx_configure
```

**Tag naming conventions** (Red Hat recommendation):

- Prefix all tags with role name to avoid conflicts
- Use meaningful, standalone tags (avoid tags that cause issues when run alone)
- Document all tags and their purposes in README

## R5: Non-Reusable Handlers (Warning)

Handlers with generic names or hardcoded services.

```yaml
# ❌ Bad
handlers:
  - name: restart service
    ansible.builtin.service:
      name: nginx
      state: restarted

# ✅ Good - explicit name and configurable service
handlers:
  - name: Restart nginx
    ansible.builtin.service:
      name: "{{ nginx_service_name | default('nginx') }}"
      state: restarted
    listen: "restart web server"
```

## R6: Business Logic in Tasks (Warning)

Complex conditions repeated instead of using computed variables.

```yaml
# ❌ Bad - repeated condition
- name: Task 1
  ansible.builtin.debug:
    msg: "Production"
  when: env == "prod" and region == "eu" and ha_enabled

- name: Task 2
  ansible.builtin.debug:
    msg: "Production"
  when: env == "prod" and region == "eu" and ha_enabled

# ✅ Good - computed variable in defaults or vars
# vars/main.yml
is_production_ha: "{{ env == 'prod' and region == 'eu' and ha_enabled }}"

# tasks/main.yml
- name: Task 1
  ansible.builtin.debug:
    msg: "Production"
  when: is_production_ha
```

## R7: Invalid Role Naming (Warning)

Role names containing dashes or invalid characters that cause issues with collections.

```text
# ❌ Bad - dashes in role names
roles/
├── web-server/        # Dash causes collection issues
├── db-manager/        # Not valid Python identifier
└── my_app-deploy/     # Mixed conventions

# ✅ Good - underscores only
roles/
├── webserver/         # Single word
├── db_manager/        # Underscore separator
└── myapp_deploy/      # Consistent naming
```

**Role naming conventions** (Red Hat recommendation):

- Use only lowercase letters, numbers, and underscores
- Avoid dashes (hyphens) - they cause issues with Ansible collections
- Role names must be valid Python identifiers
- Keep names concise but descriptive
