# Security Rules

Evaluate security practices and vulnerabilities in Ansible roles.

## SEC1: Hardcoded Secrets (Critical)

Passwords, API keys, tokens, or other sensitive data hardcoded in playbooks or variables.

```yaml
# ❌ Bad - Hardcoded credentials
- name: Create user
  ansible.builtin.user:
    name: admin
    password: "P@ssw0rd123"

# ❌ Bad - Hardcoded API keys
vars:
  api_key: "sk-1234567890abcdef"
  aws_secret_key: "AKIAIOSFODNN7EXAMPLE"
  db_password: "secret123"

# ✅ Good - Use Ansible Vault
- name: Create user
  ansible.builtin.user:
    name: admin
    password: "{{ admin_password | password_hash('sha512') }}"
  no_log: true

# ✅ Good - Load vaulted variables
- name: Include vaulted vars
  ansible.builtin.include_vars:
    file: secrets.yml  # Encrypted with ansible-vault

# ✅ Good - Use external secret management
- name: Fetch secret from HashiCorp Vault
  ansible.builtin.set_fact:
    db_password: "{{ lookup('hashi_vault', 'secret=secret/data/db:password') }}"
  no_log: true
```

**Check for**: Patterns like `password:`, `api_key:`, `secret:`, `token:`, `key:` followed by literal strings.

## SEC2: Missing no_log (Warning)

Tasks handling sensitive data without `no_log: true`, exposing secrets in logs.

```yaml
# ❌ Bad - Secrets visible in logs
- name: Set database password
  ansible.builtin.set_fact:
    db_password: "{{ vault_db_password }}"

- name: Configure API
  ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config.yml
  vars:
    api_key: "{{ vault_api_key }}"

# ✅ Good - Secrets hidden from logs
- name: Set database password
  ansible.builtin.set_fact:
    db_password: "{{ vault_db_password }}"
  no_log: true

- name: Configure API
  ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config.yml
  vars:
    api_key: "{{ vault_api_key }}"
  no_log: true
```

**Check for**: Tasks using variables with names containing `password`, `secret`, `key`, `token`, `credential` without `no_log: true`.

## SEC3: Excessive Privilege Escalation (Warning)

Using `become: yes` at playbook level or when not necessary.

```yaml
# ❌ Bad - Entire playbook runs as root
- hosts: all
  become: yes
  become_user: root
  tasks:
    - name: Check application status
      ansible.builtin.command: systemctl status myapp

    - name: Read configuration
      ansible.builtin.slurp:
        src: /etc/myapp/config.yml

# ✅ Good - Only escalate when necessary
- hosts: all
  tasks:
    - name: Check application status
      ansible.builtin.command: systemctl status myapp
      # No become needed for read-only systemctl

    - name: Install package
      ansible.builtin.apt:
        name: nginx
        state: present
      become: yes
      # Only escalate for this task

    - name: Configure application
      ansible.builtin.template:
        src: config.j2
        dest: /etc/myapp/config.yml
        owner: myapp
        group: myapp
        mode: '0640'
      become: yes
```

**Principle of least privilege**: Only use `become` on tasks that require it, not at play level.

## SEC4: Insecure File Permissions (Critical)

Missing or overly permissive file permissions.

```yaml
# ❌ Bad - World-readable private key
- name: Create SSH key
  ansible.builtin.copy:
    src: id_rsa
    dest: /home/user/.ssh/id_rsa
    mode: '0644'

# ❌ Bad - World-writable script
- name: Create script
  ansible.builtin.copy:
    src: deploy.sh
    dest: /usr/local/bin/deploy.sh
    mode: '0777'

# ❌ Bad - Missing mode (depends on umask)
- name: Create config file
  ansible.builtin.template:
    src: database.conf.j2
    dest: /etc/app/database.conf

# ✅ Good - Proper permissions
- name: Create SSH key
  ansible.builtin.copy:
    src: id_rsa
    dest: /home/user/.ssh/id_rsa
    owner: user
    group: user
    mode: '0600'

- name: Create config file
  ansible.builtin.template:
    src: database.conf.j2
    dest: /etc/app/database.conf
    owner: appuser
    group: appgroup
    mode: '0640'

- name: Create secure directory
  ansible.builtin.file:
    path: /etc/app/secrets
    state: directory
    owner: appuser
    group: appgroup
    mode: '0750'
```

**Permission guidelines**:

| File Type | Mode | Owner | Group |
|-----------|------|-------|-------|
| Private keys | 0600 | user | user |
| Public keys | 0644 | user | user |
| Config files (sensitive) | 0640 | app | app |
| Config files (public) | 0644 | app | app |
| Executables | 0755 | root | root |
| Directories (sensitive) | 0750 | app | app |
| Directories (public) | 0755 | app | app |

## SEC5: Command Injection Vulnerability (Critical)

Unvalidated user input in shell/command modules.

```yaml
# ❌ Bad - Command injection vulnerability
- name: Process user file
  ansible.builtin.shell: "cat {{ user_provided_filename }}"
  # User could provide "; rm -rf /"

# ❌ Bad - Unvalidated search term
- name: Search logs
  ansible.builtin.command: "grep {{ search_term }} /var/log/app.log"

# ✅ Good - Use quote filter
- name: Process user file
  ansible.builtin.shell: "cat {{ user_provided_filename | quote }}"
  when: user_provided_filename is match('^[a-zA-Z0-9._-]+$')

# ✅ Better - Use modules instead of shell
- name: Read file content
  ansible.builtin.slurp:
    src: "{{ user_provided_filename }}"
  register: file_content
  when: user_provided_filename is match('^[a-zA-Z0-9._-]+$')

# ✅ Good - Validate input before use
- name: Search logs
  ansible.builtin.command: "grep {{ search_term | quote }} /var/log/app.log"
  when:
    - search_term is defined
    - search_term | length > 0
    - search_term is match('^[a-zA-Z0-9 ]+$')
```

**Best practices**:

- Prefer modules over command/shell whenever possible
- Always use `quote` filter for variables in shell commands
- Validate input with regex patterns (whitelist, not blacklist)

## SEC6: Insecure Network Configuration (Warning)

Using HTTP instead of HTTPS, disabling SSL verification, or exposing services on all interfaces.

```yaml
# ❌ Bad - HTTP instead of HTTPS
- name: Download file
  ansible.builtin.get_url:
    url: http://example.com/file.tar.gz
    dest: /tmp/file.tar.gz

# ❌ Bad - SSL verification disabled
- name: Call API
  ansible.builtin.uri:
    url: https://api.example.com/data
    validate_certs: no

# ❌ Bad - Service exposed on all interfaces
- name: Configure service
  ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config.yml
  vars:
    bind_address: "0.0.0.0"

# ✅ Good - HTTPS with checksum verification
- name: Download file
  ansible.builtin.get_url:
    url: https://example.com/file.tar.gz
    dest: /tmp/file.tar.gz
    checksum: sha256:abc123def456...

# ✅ Good - SSL validation enabled
- name: Call API
  ansible.builtin.uri:
    url: https://api.example.com/data
    validate_certs: yes
    client_cert: /path/to/cert.pem
    client_key: /path/to/key.pem

# ✅ Good - Bind to specific interface
- name: Configure service
  ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config.yml
  vars:
    bind_address: "127.0.0.1"
```

## SEC7: Disabled Security Features (Critical)

Disabling SELinux, AppArmor, or other security mechanisms.

```yaml
# ❌ Bad - Disabling SELinux
- name: Disable SELinux
  ansible.posix.selinux:
    state: disabled

- name: Set SELinux permissive
  ansible.posix.selinux:
    policy: targeted
    state: permissive

# ✅ Good - Keep SELinux enforcing
- name: Configure SELinux
  ansible.posix.selinux:
    policy: targeted
    state: enforcing

# ✅ Good - Set proper SELinux contexts
- name: Set SELinux context for web content
  community.general.sefcontext:
    target: '/web/content(/.*)?'
    setype: httpd_sys_content_t
    state: present

- name: Apply SELinux context
  ansible.builtin.command: restorecon -Rv /web/content
```

**Check for**: `selinux: disabled`, `selinux: permissive`, `apparmor: disabled`.

## SEC8: Missing Firewall Rules (Info)

Services exposed without firewall configuration.

```yaml
# ✅ Good - Configure firewall rules
- name: Allow HTTPS from internal network
  community.general.ufw:
    rule: allow
    port: '443'
    proto: tcp
    src: '10.0.0.0/8'

- name: Deny all other incoming
  community.general.ufw:
    rule: deny
    direction: incoming
    default: yes
```

## SEC9: Unsafe Temporary Files (Warning)

Creating temporary files in world-writable directories without proper permissions.

```yaml
# ❌ Bad - Predictable temp file, insecure permissions
- name: Create temp file
  ansible.builtin.copy:
    content: "{{ sensitive_data }}"
    dest: /tmp/myapp_config

# ✅ Good - Use tempfile module with secure defaults
- name: Create secure temp file
  ansible.builtin.tempfile:
    state: file
    suffix: .conf
  register: temp_config

- name: Write to temp file
  ansible.builtin.copy:
    content: "{{ sensitive_data }}"
    dest: "{{ temp_config.path }}"
    mode: '0600'
  no_log: true
```

## SEC10: Missing Input Validation (Warning)

Using variables from external sources without validation.

```yaml
# ❌ Bad - No validation of external input
- name: Create user from inventory
  ansible.builtin.user:
    name: "{{ user_name }}"
    uid: "{{ user_uid }}"
    shell: "{{ user_shell }}"

# ✅ Good - Validate before use
- name: Validate user parameters
  ansible.builtin.assert:
    that:
      - user_name is match('^[a-z_][a-z0-9_-]*$')
      - user_uid | int > 1000
      - user_shell in ['/bin/bash', '/bin/sh', '/usr/sbin/nologin']
    fail_msg: "Invalid user parameters provided"

- name: Create user from inventory
  ansible.builtin.user:
    name: "{{ user_name }}"
    uid: "{{ user_uid }}"
    shell: "{{ user_shell }}"
```

## Security Checklist

Before running playbooks in production, verify:

- [ ] No hardcoded secrets (passwords, API keys, tokens)
- [ ] All sensitive data encrypted with Ansible Vault
- [ ] `no_log: true` used for tasks handling secrets
- [ ] Privilege escalation only where necessary
- [ ] File permissions explicitly set (not relying on umask)
- [ ] Private keys have mode 0600
- [ ] No world-writable files or directories
- [ ] Input validation for user-provided variables
- [ ] Using modules instead of shell/command where possible
- [ ] Quote filter used for variables in shell commands
- [ ] HTTPS used instead of HTTP
- [ ] SSL certificate validation enabled
- [ ] Services bound to specific interfaces, not 0.0.0.0
- [ ] SELinux/AppArmor not disabled
- [ ] Firewall rules configured appropriately
