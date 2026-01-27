# Task Best Practices Rules

Evaluate task quality, naming, idempotency, error handling, and Jinja2 usage.

## T1: Missing or Poor Task Names (Warning)

Tasks without names or with vague, uninformative names.

```yaml
# ❌ Bad - No name
- ansible.builtin.apt:
    name: nginx

# ❌ Bad - Vague names
- name: Install package
  ansible.builtin.apt:
    name: nginx

- name: Configure
  ansible.builtin.template:
    src: vhost.conf.j2
    dest: /etc/nginx/sites-available/example.com

- name: Service
  ansible.builtin.systemd:
    name: nginx
    state: started

# ✅ Good - Descriptive, action-oriented names
- name: Install nginx web server
  ansible.builtin.apt:
    name: nginx
    state: present

- name: Configure nginx virtual host for example.com
  ansible.builtin.template:
    src: vhost.conf.j2
    dest: /etc/nginx/sites-available/example.com

- name: Enable and start nginx service
  ansible.builtin.systemd:
    name: nginx
    state: started
    enabled: yes

- name: Create application user with limited privileges
  ansible.builtin.user:
    name: appuser
    system: yes
    shell: /bin/false
    home: /var/lib/app
```

**Naming conventions**:

- Always name your tasks - makes output readable
- Use action verbs: Install, Configure, Enable, Create, Remove, Update, etc.
- Be specific - mention what is being installed/configured
- Keep names concise but clear
- Use consistent naming across all tasks

**Sub-task file naming** (Red Hat recommendation):

```yaml
# tasks/install.yml - Prefix with file identifier for clarity in logs
- name: install | Install required packages
  ansible.builtin.apt:
    name: "{{ myapp_packages }}"
    state: present

- name: install | Create application directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
  loop: "{{ myapp_directories }}"

# tasks/configure.yml
- name: configure | Deploy configuration file
  ansible.builtin.template:
    src: config.j2
    dest: /etc/myapp/config.yml

- name: configure | Set up environment variables
  ansible.builtin.template:
    src: env.j2
    dest: /etc/myapp/env
```

This clarifies which file each task belongs to in complex multi-file roles.

## T2: Non-Idempotent Tasks (Warning)

Tasks that make changes on every run instead of only when needed.

```yaml
# ❌ Bad - Command without creates/removes (runs every time)
- name: Download file
  ansible.builtin.command: curl -o /tmp/file.tar.gz https://example.com/file.tar.gz

# ❌ Bad - Shell appending to file (duplicates on every run)
- name: Add line to bashrc
  ansible.builtin.shell: echo "export PATH=$PATH:/opt/bin" >> ~/.bashrc

# ❌ Bad - Always reports changed
- name: Check service status
  ansible.builtin.command: systemctl status myapp
  register: service_status

# ✅ Good - Use creates parameter
- name: Download file
  ansible.builtin.command: curl -o /tmp/file.tar.gz https://example.com/file.tar.gz
  args:
    creates: /tmp/file.tar.gz

# ✅ Better - Use get_url module (inherently idempotent)
- name: Download file
  ansible.builtin.get_url:
    url: https://example.com/file.tar.gz
    dest: /tmp/file.tar.gz
    checksum: sha256:abc123...

# ✅ Good - Use lineinfile module (idempotent)
- name: Add PATH to bashrc
  ansible.builtin.lineinfile:
    path: ~/.bashrc
    line: 'export PATH=$PATH:/opt/bin'
    create: yes

# ✅ Good - Use changed_when for read-only commands
- name: Check service status
  ansible.builtin.command: systemctl status myapp
  register: service_status
  changed_when: false
  failed_when: service_status.rc not in [0, 3]
```

**Idempotency best practices**:

- Use modules instead of command/shell whenever possible
- Use `creates` or `removes` parameters for command/shell when necessary
- Set `changed_when: false` for read-only commands
- Test idempotency: run playbook twice, second run should show no changes

## T3: Missing Error Handling (Warning)

Tasks without proper error handling using blocks, rescue, and always.

```yaml
# ❌ Bad - No error handling for risky operations
- name: Run database migration
  ansible.builtin.command: /usr/local/bin/migrate.sh

- name: Restart service
  ansible.builtin.systemd:
    name: myapp
    state: restarted

# ✅ Good - Use blocks for error handling
- name: Deploy application with rollback capability
  block:
    - name: Stop application service
      ansible.builtin.systemd:
        name: myapp
        state: stopped

    - name: Run database migration
      ansible.builtin.command: /usr/local/bin/migrate.sh
      register: migration_result

    - name: Deploy new application version
      ansible.builtin.copy:
        src: "{{ app_package }}"
        dest: /opt/myapp/

    - name: Start application service
      ansible.builtin.systemd:
        name: myapp
        state: started

  rescue:
    - name: Log deployment failure
      ansible.builtin.debug:
        msg: "Deployment failed: {{ migration_result.stderr | default('unknown error') }}"

    - name: Rollback to previous version
      ansible.builtin.copy:
        src: /opt/myapp/backup/
        dest: /opt/myapp/
        remote_src: yes

    - name: Start application with previous version
      ansible.builtin.systemd:
        name: myapp
        state: started

  always:
    - name: Clean up temporary files
      ansible.builtin.file:
        path: /tmp/deployment.lock
        state: absent

    - name: Send notification
      ansible.builtin.uri:
        url: "{{ notification_webhook }}"
        method: POST
        body_format: json
        body:
          status: "{{ 'failed' if ansible_failed_task is defined else 'success' }}"
      when: notification_webhook is defined
```

## T4: Improper Use of ignore_errors (Warning)

Using `ignore_errors: yes` without proper justification or alternative.

```yaml
# ❌ Bad - Blindly ignoring errors
- name: Stop old service
  ansible.builtin.systemd:
    name: old-service
    state: stopped
  ignore_errors: yes

# ✅ Good - Check first, then act conditionally
- name: Check if old service exists
  ansible.builtin.systemd:
    name: old-service
  register: old_service_status
  failed_when: false

- name: Stop old service if it exists
  ansible.builtin.systemd:
    name: old-service
    state: stopped
  when: old_service_status.status.ActiveState is defined

# ✅ Acceptable - When failure is genuinely expected and handled
- name: Try to remove optional package
  ansible.builtin.apt:
    name: optional-debug-tools
    state: absent
  ignore_errors: yes
  register: remove_result

- name: Log if optional package removal failed
  ansible.builtin.debug:
    msg: "Optional package removal failed (non-critical): {{ remove_result.msg }}"
  when: remove_result is failed
```

## T5: Missing Check Mode Support (Info)

Tasks that don't work correctly in check mode (dry-run).

```yaml
# ❌ Bad - Breaks check mode by requiring previous task results
- name: Get application version
  ansible.builtin.command: /opt/myapp/bin/version
  register: app_version

- name: Configure based on version
  ansible.builtin.template:
    src: config.j2
    dest: /etc/myapp/config.yml
  vars:
    version: "{{ app_version.stdout }}"
  # Fails in check mode because app_version.stdout doesn't exist

# ✅ Good - Handle check mode gracefully
- name: Get application version
  ansible.builtin.command: /opt/myapp/bin/version
  register: app_version
  check_mode: no  # Always run, even in check mode
  changed_when: false

- name: Configure based on version
  ansible.builtin.template:
    src: config.j2
    dest: /etc/myapp/config.yml
  vars:
    version: "{{ app_version.stdout | default('unknown') }}"

# ✅ Good - Skip complex operations in check mode
- name: Apply complex database changes
  ansible.builtin.command: /usr/local/bin/complex-migration.sh
  when: not ansible_check_mode
```

## T6: Poor Template Practices (Warning)

Templates without comments, with complex logic, or missing variable validation.

```yaml
# ❌ Bad template (config.j2)
user {{ user }}
port {{ port }}
{% for item in items %}
{{ item }}
{% endfor %}
```

```jinja2
{# ✅ Good template (config.j2) #}
{{ ansible_managed | comment }}
{# Template: roles/myapp/templates/config.j2 #}

# User configuration
user {{ myapp_user | default('appuser') }}
port {{ myapp_port | default(8080) }}

{# Database settings #}
{% if myapp_database_host is defined %}
database_host = {{ myapp_database_host }}
database_port = {{ myapp_database_port | default(5432) }}
database_name = {{ myapp_database_name | mandatory }}
{% endif %}

{# Feature flags #}
{% for feature, enabled in myapp_features.items() | default({}) %}
feature.{{ feature }} = {{ enabled | lower }}
{% endfor %}

{# Server list #}
{% if myapp_servers is defined and myapp_servers | length > 0 %}
servers = {{ myapp_servers | join(',') }}
{% else %}
servers = localhost
{% endif %}
```

**Template best practices** (Red Hat recommendations):

- Use `{{ ansible_managed | comment }}` at template top (auto-generates management notice)
- Avoid timestamps like `{{ ansible_date_time.date }}` (causes false changes on every run)
- Use `default` filter for optional variables
- Use `mandatory` filter for required variables
- Comment complex Jinja2 logic
- Use `backup: true` in template tasks to preserve previous versions

```yaml
# ✅ Good - Template task with backup
- name: Configure application
  ansible.builtin.template:
    src: config.j2
    dest: /etc/myapp/config.yml
    owner: myapp
    group: myapp
    mode: '0640'
    backup: true
  notify: Restart myapp
```

**Use role_path for includes** (prevents unintended file discovery):

```yaml
# ✅ Good - Explicit path to role files
- name: Include role-specific variables
  ansible.builtin.include_vars:
    file: "{{ role_path }}/vars/{{ ansible_os_family }}.yml"

# ❌ Bad - May find files from parent roles
- name: Include variables
  ansible.builtin.include_vars:
    file: "vars/{{ ansible_os_family }}.yml"
```

## T7: Unsafe Loop Practices (Info)

Inefficient or problematic loop usage.

```yaml
# ❌ Bad - Installing packages one by one (slow)
- name: Install packages
  ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  loop:
    - nginx
    - python3
    - git
    - curl

# ✅ Good - Install all packages at once
- name: Install required packages
  ansible.builtin.apt:
    name:
      - nginx
      - python3
      - git
      - curl
    state: present

# ❌ Bad - Loop without loop_control for large lists
- name: Create many users
  ansible.builtin.user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
  loop: "{{ large_user_list }}"

# ✅ Good - Use loop_control for better output
- name: Create users
  ansible.builtin.user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
  loop: "{{ users }}"
  loop_control:
    label: "{{ item.name }}"
    pause: 1  # Optional: pause between iterations

# ✅ Good - Use extended loop variables when needed
- name: Process items with index
  ansible.builtin.debug:
    msg: "Processing {{ item }} ({{ ansible_loop.index }} of {{ ansible_loop.length }})"
  loop: "{{ items }}"
  loop_control:
    extended: true
```

## T8: Complex Conditionals (Info)

Overly complex or repeated conditional logic.

```yaml
# ❌ Bad - Complex repeated condition
- name: Task 1
  ansible.builtin.debug:
    msg: "Production EU HA"
  when: env == "prod" and region == "eu" and ha_enabled and not maintenance_mode

- name: Task 2
  ansible.builtin.debug:
    msg: "Production EU HA"
  when: env == "prod" and region == "eu" and ha_enabled and not maintenance_mode

# ✅ Good - Use computed variable
# vars/main.yml or set_fact
is_production_ha: >-
  {{ env == 'prod' and
     region == 'eu' and
     ha_enabled | default(false) and
     not maintenance_mode | default(false) }}

# tasks/main.yml
- name: Task 1
  ansible.builtin.debug:
    msg: "Production EU HA"
  when: is_production_ha

- name: Task 2
  ansible.builtin.debug:
    msg: "Production EU HA"
  when: is_production_ha

# ✅ Good - Use block to group conditional tasks
- name: Production HA configuration
  when: is_production_ha
  block:
    - name: Task 1
      ansible.builtin.debug:
        msg: "Production EU HA"

    - name: Task 2
      ansible.builtin.debug:
        msg: "Production EU HA"
```

## T9: Missing Handlers Notification (Warning)

Configuration changes without notifying handlers for service restart/reload.

```yaml
# ❌ Bad - Config change without handler notification
- name: Update nginx configuration
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  # Service won't reload to pick up changes!

# ✅ Good - Notify handler on change
- name: Update nginx configuration
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  notify:
    - Validate nginx configuration
    - Reload nginx

# handlers/main.yml
- name: Validate nginx configuration
  ansible.builtin.command: nginx -t
  changed_when: false

- name: Reload nginx
  ansible.builtin.systemd:
    name: nginx
    state: reloaded
```

## T10: Insecure Jinja2 Defaults (Warning)

Using unsafe defaults that could lead to security issues.

```yaml
# ❌ Bad - Empty/weak defaults for security-sensitive values
- name: Configure SSH
  ansible.builtin.template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config
  vars:
    ssh_permit_root_login: "{{ permit_root | default('yes') }}"
    ssh_password_auth: "{{ password_auth | default('yes') }}"

# ✅ Good - Secure defaults
- name: Configure SSH
  ansible.builtin.template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config
  vars:
    ssh_permit_root_login: "{{ permit_root | default('no') }}"
    ssh_password_auth: "{{ password_auth | default('no') }}"
    ssh_port: "{{ ssh_custom_port | default(22) }}"
```

## T11: Debug Without Verbosity (Info)

Debug statements without verbosity parameter cluttering production logs.

```yaml
# ❌ Bad - Debug always shown in output
- name: Show configuration values
  ansible.builtin.debug:
    var: myapp_config

- name: Debug deployment status
  ansible.builtin.debug:
    msg: "Deploying version {{ myapp_version }} to {{ inventory_hostname }}"

# ✅ Good - Debug only shown with increased verbosity (-v, -vv, etc.)
- name: Show configuration values
  ansible.builtin.debug:
    var: myapp_config
    verbosity: 1  # Shown with -v

- name: Debug deployment status
  ansible.builtin.debug:
    msg: "Deploying version {{ myapp_version }} to {{ inventory_hostname }}"
    verbosity: 2  # Shown with -vv

- name: Detailed internal state (development only)
  ansible.builtin.debug:
    var: __myapp_internal_state
    verbosity: 3  # Shown with -vvv
```

**Verbosity levels**:

- `verbosity: 1` (-v): Basic diagnostic information
- `verbosity: 2` (-vv): Detailed debugging
- `verbosity: 3` (-vvv): Internal state/development only

## T12: Deprecated Facts Notation (Info)

Using old `ansible_*` variable notation instead of `ansible_facts[]` dictionary.

```yaml
# ❌ Bad - Old notation (deprecated)
- name: Install package on Debian
  ansible.builtin.apt:
    name: nginx
  when: ansible_os_family == "Debian"

- name: Show distribution
  ansible.builtin.debug:
    msg: "Running on {{ ansible_distribution }} {{ ansible_distribution_version }}"

# ✅ Good - Bracket notation with ansible_facts
- name: Install package on Debian
  ansible.builtin.apt:
    name: nginx
  when: ansible_facts['os_family'] == "Debian"

- name: Show distribution
  ansible.builtin.debug:
    msg: "Running on {{ ansible_facts['distribution'] }} {{ ansible_facts['distribution_version'] }}"

# ✅ Good - Handle gather_facts: false scenarios
- name: Ensure facts are available
  ansible.builtin.setup:
    gather_subset:
      - min
  when: ansible_facts['os_family'] is not defined
```

**Benefits of bracket notation**:

- More explicit and consistent
- Works better with `INJECT_FACTS_AS_VARS=false` setting
- Follows Red Hat recommended practices
- Clearer distinction between facts and other variables
