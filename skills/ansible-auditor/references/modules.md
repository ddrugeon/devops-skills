# Module Usage Rules

Evaluate proper module usage, FQCN compliance, and deprecated module detection.

## MOD1: Missing FQCN (Warning)

Modules used without Fully Qualified Collection Name (FQCN).

```yaml
# ❌ Bad - Short names (deprecated style)
- name: Install nginx
  apt:
    name: nginx
    state: present

- name: Copy config
  copy:
    src: nginx.conf
    dest: /etc/nginx/nginx.conf

- name: Start service
  service:
    name: nginx
    state: started

# ✅ Good - FQCN (recommended)
- name: Install nginx
  ansible.builtin.apt:
    name: nginx
    state: present

- name: Copy config
  ansible.builtin.copy:
    src: nginx.conf
    dest: /etc/nginx/nginx.conf

- name: Start service
  ansible.builtin.service:
    name: nginx
    state: started
```

**Why use FQCN**:

- Clarity: Explicitly shows which collection provides the module
- Conflict prevention: Avoids naming conflicts between collections
- Future-proofing: Prevents breakage when modules move between collections
- Best practice: Recommended by Ansible for all playbooks (Ansible 2.10+)

## MOD2: Deprecated Modules (Critical)

Using modules that have been deprecated or moved to collections.

### Package Management

| Deprecated | Replacement | Notes |
| ---------- | ----------- | ----- |
| `easy_install` | `ansible.builtin.pip` | easy_install deprecated in Python |
| `homebrew` | `community.general.homebrew` | Moved to community.general |
| `zypper` | `community.general.zypper` | Moved to community.general |
| `apk` | `community.general.apk` | Moved to community.general |

### File Operations

| Deprecated | Replacement | Notes |
| ---------- | ----------- | ----- |
| `synchronize` | `ansible.posix.synchronize` | Moved to ansible.posix |
| `acl` | `ansible.posix.acl` | Moved to ansible.posix |

### User Management

| Deprecated | Replacement | Notes |
| ---------- | ----------- | ----- |
| `authorized_key` | `ansible.posix.authorized_key` | Moved to ansible.posix |

### Networking

| Deprecated | Replacement | Notes |
| ---------- | ----------- | ----- |
| `ufw` | `community.general.ufw` | Moved to community.general |
| `firewalld` | `ansible.posix.firewalld` | Moved to ansible.posix |

### Cloud Providers

| Deprecated | Replacement | Notes |
| ---------- | ----------- | ----- |
| `ec2` | `amazon.aws.ec2_instance` | Use amazon.aws collection |
| `ec2_ami` | `amazon.aws.ec2_ami` | Use amazon.aws collection |
| `ec2_vpc` | `amazon.aws.ec2_vpc_net` | Use amazon.aws collection |
| `azure_rm_*` | `azure.azcollection.*` | Use azure.azcollection |
| `gcp_*` | `google.cloud.*` | Use google.cloud collection |
| `docker_container` | `community.docker.docker_container` | Use community.docker |
| `docker_image` | `community.docker.docker_image` | Use community.docker |

### Database

| Deprecated | Replacement | Notes |
| ---------- | ----------- | ----- |
| `mysql_db` | `community.mysql.mysql_db` | Use community.mysql |
| `mysql_user` | `community.mysql.mysql_user` | Use community.mysql |
| `postgresql_db` | `community.postgresql.postgresql_db` | Use community.postgresql |
| `postgresql_user` | `community.postgresql.postgresql_user` | Use community.postgresql |

### Container & Orchestration

| Deprecated | Replacement | Notes |
|------------|-------------|-------|
| `docker_container` | `community.docker.docker_container` | Moved in Ansible 2.10 |
| `docker_image` | `community.docker.docker_image` | Moved in Ansible 2.10 |
| `docker_network` | `community.docker.docker_network` | Moved in Ansible 2.10 |
| `docker_volume` | `community.docker.docker_volume` | Moved in Ansible 2.10 |
| `docker_swarm` | `community.docker.docker_swarm` | Moved in Ansible 2.10 |
| `k8s` | `kubernetes.core.k8s` | Moved in Ansible 2.10 |
| `k8s_info` | `kubernetes.core.k8s_info` | Moved in Ansible 2.10 |
| `k8s_scale` | `kubernetes.core.k8s_scale` | Moved in Ansible 2.10 |
| `helm` | `kubernetes.core.helm` | Moved in Ansible 2.10 |

### HashiCorp Vault

| Deprecated | Replacement | Notes |
|------------|-------------|-------|
| `hashi_vault` lookup | `community.hashi_vault.hashi_vault` | Moved in Ansible 2.10 |

## MOD3: Shell/Command Instead of Module (Warning)

Using shell or command modules when a dedicated module exists.

```yaml
# ❌ Bad - Using shell when module exists
- name: Install package
  ansible.builtin.shell: apt-get install -y nginx

- name: Create directory
  ansible.builtin.command: mkdir -p /etc/myapp

- name: Create user
  ansible.builtin.shell: useradd -m -s /bin/bash appuser

- name: Start service
  ansible.builtin.command: systemctl start nginx

- name: Download file
  ansible.builtin.shell: curl -o /tmp/file.tar.gz https://example.com/file.tar.gz

# ✅ Good - Using appropriate modules
- name: Install package
  ansible.builtin.apt:
    name: nginx
    state: present

- name: Create directory
  ansible.builtin.file:
    path: /etc/myapp
    state: directory
    mode: '0755'

- name: Create user
  ansible.builtin.user:
    name: appuser
    shell: /bin/bash
    create_home: yes

- name: Start service
  ansible.builtin.systemd:
    name: nginx
    state: started

- name: Download file
  ansible.builtin.get_url:
    url: https://example.com/file.tar.gz
    dest: /tmp/file.tar.gz
```

**Common replacements**:

| Shell Command | Module Alternative |
|---------------|-------------------|
| `apt-get`, `yum`, `dnf` | `ansible.builtin.apt`, `ansible.builtin.yum`, `ansible.builtin.dnf` |
| `mkdir`, `rm`, `chmod`, `chown` | `ansible.builtin.file` |
| `useradd`, `usermod`, `userdel` | `ansible.builtin.user` |
| `groupadd`, `groupmod` | `ansible.builtin.group` |
| `systemctl`, `service` | `ansible.builtin.systemd`, `ansible.builtin.service` |
| `curl`, `wget` | `ansible.builtin.get_url`, `ansible.builtin.uri` |
| `cp`, `mv` | `ansible.builtin.copy`, `ansible.builtin.fetch` |
| `ln -s` | `ansible.builtin.file` with `state: link` |
| `mount` | `ansible.posix.mount` |
| `crontab` | `ansible.builtin.cron` |
| `sysctl` | `ansible.posix.sysctl` |

## MOD4: Undeclared Collection Dependencies (Warning)

Using modules from collections without declaring them in `meta/main.yml` or `requirements.yml`.

```yaml
# ❌ Bad - Using community module without declaration
- name: Configure firewall
  community.general.ufw:
    rule: allow
    port: '443'

# tasks/main.yml uses community.docker but it's not declared
- name: Run container
  community.docker.docker_container:
    name: myapp
    image: myapp:latest
```

```yaml
# ✅ Good - Declare in meta/main.yml
# meta/main.yml
collections:
  - community.general
  - community.docker
  - ansible.posix

# ✅ Good - Or use collections/requirements.yml
# collections/requirements.yml
collections:
  - name: community.general
    version: ">=6.0.0"
  - name: community.docker
    version: ">=3.0.0"
  - name: ansible.posix
    version: ">=1.5.0"
```

## MOD5: Outdated Module Syntax (Info)

Using old module parameter names or deprecated syntax.

```yaml
# ❌ Bad - Old syntax
- name: Install package
  ansible.builtin.apt:
    pkg: nginx  # Deprecated parameter name
    state: installed  # Old state value

- name: Copy file
  ansible.builtin.copy:
    src: file.txt
    dest: /tmp/file.txt
    remote_src: True  # Old boolean style

# ✅ Good - Current syntax
- name: Install package
  ansible.builtin.apt:
    name: nginx  # Current parameter name
    state: present  # Current state value

- name: Copy file
  ansible.builtin.copy:
    src: file.txt
    dest: /tmp/file.txt
    remote_src: true  # YAML boolean
```

## MOD6: Missing Changed_When/Failed_When (Warning)

Command/shell modules without proper result handling.

```yaml
# ❌ Bad - Always reports changed
- name: Check if file exists
  ansible.builtin.command: test -f /etc/myapp/config.yml

- name: Get current version
  ansible.builtin.shell: myapp --version

# ✅ Good - Proper result handling
- name: Check if file exists
  ansible.builtin.command: test -f /etc/myapp/config.yml
  register: file_check
  changed_when: false
  failed_when: false

- name: Get current version
  ansible.builtin.shell: myapp --version
  register: version_output
  changed_when: false

- name: Run migration
  ansible.builtin.command: myapp migrate
  register: migration_result
  changed_when: "'migrated' in migration_result.stdout"
  failed_when: migration_result.rc != 0 and 'already migrated' not in migration_result.stderr
```

## MOD7: Using Raw Module Unnecessarily (Info)

Using `raw` module when `command` or `shell` would work.

```yaml
# ❌ Bad - Raw when not needed
- name: Check uptime
  ansible.builtin.raw: uptime

# ✅ Good - Use command
- name: Check uptime
  ansible.builtin.command: uptime
  changed_when: false

# ✅ Acceptable - Raw for bootstrap (no Python)
- name: Install Python on minimal system
  ansible.builtin.raw: apt-get update && apt-get install -y python3
  when: ansible_python_interpreter is not defined
```

**When to use raw**:

- Bootstrapping systems without Python
- Network devices with limited shell support
- Very early provisioning stages

## FQCN Reference

### ansible.builtin (Core Modules)

| Module | Description |
|--------|-------------|
| `ansible.builtin.apt` | Debian/Ubuntu package management |
| `ansible.builtin.apt_key` | Add or remove apt key |
| `ansible.builtin.apt_repository` | Manage apt repositories |
| `ansible.builtin.yum` | RHEL/CentOS package management |
| `ansible.builtin.yum_repository` | Manage yum repositories |
| `ansible.builtin.dnf` | Fedora/RHEL 8+ package management |
| `ansible.builtin.dnf5` | RHEL 9+/Fedora package management (new) |
| `ansible.builtin.package` | Generic package management |
| `ansible.builtin.pip` | Python package management |
| `ansible.builtin.copy` | Copy files to remote |
| `ansible.builtin.fetch` | Fetch files from remote |
| `ansible.builtin.file` | File/directory management |
| `ansible.builtin.find` | Find files based on criteria |
| `ansible.builtin.template` | Template files |
| `ansible.builtin.lineinfile` | Manage lines in files |
| `ansible.builtin.blockinfile` | Manage blocks in files |
| `ansible.builtin.user` | User management |
| `ansible.builtin.group` | Group management |
| `ansible.builtin.hostname` | Manage hostname |
| `ansible.builtin.service` | Service management |
| `ansible.builtin.systemd_service` | Systemd service management (canonical name) |
| `ansible.builtin.reboot` | Reboot machine |
| `ansible.builtin.cron` | Cron job management |
| `ansible.builtin.command` | Execute commands |
| `ansible.builtin.shell` | Execute shell commands |
| `ansible.builtin.raw` | Low-level command execution |
| `ansible.builtin.script` | Run local scripts remotely |
| `ansible.builtin.get_url` | Download files |
| `ansible.builtin.uri` | HTTP requests |
| `ansible.builtin.git` | Git operations |
| `ansible.builtin.unarchive` | Extract archives |
| `ansible.builtin.stat` | File statistics |
| `ansible.builtin.slurp` | Read file content |
| `ansible.builtin.wait_for` | Wait for condition |
| `ansible.builtin.debug` | Debug output |
| `ansible.builtin.assert` | Assertions |
| `ansible.builtin.fail` | Fail with message |
| `ansible.builtin.pause` | Pause playbook execution |
| `ansible.builtin.set_fact` | Set variables |
| `ansible.builtin.include_vars` | Include variables |
| `ansible.builtin.include_tasks` | Include tasks |
| `ansible.builtin.import_tasks` | Import tasks |
| `ansible.builtin.include_role` | Include role |
| `ansible.builtin.import_role` | Import role |

### ansible.posix

| Module | Description |
|--------|-------------|
| `ansible.posix.acl` | ACL management |
| `ansible.posix.at` | Schedule commands |
| `ansible.posix.authorized_key` | SSH authorized keys |
| `ansible.posix.firewalld` | Firewalld management |
| `ansible.posix.firewalld_info` | Gather firewalld information |
| `ansible.posix.mount` | Mount filesystems |
| `ansible.posix.patch` | Apply patches |
| `ansible.posix.rhel_facts` | RHEL-specific facts |
| `ansible.posix.rhel_rpm_ostree` | RHEL rpm-ostree packages |
| `ansible.posix.rpm_ostree_upgrade` | rpm-ostree system updates |
| `ansible.posix.seboolean` | SELinux booleans |
| `ansible.posix.selinux` | SELinux state |
| `ansible.posix.synchronize` | Rsync wrapper |
| `ansible.posix.sysctl` | Sysctl settings |

### community.general

| Module | Description |
|--------|-------------|
| `community.general.ufw` | UFW firewall management |
| `community.general.homebrew` | macOS Homebrew packages |
| `community.general.homebrew_cask` | macOS Homebrew casks |
| `community.general.homebrew_tap` | macOS Homebrew taps |
| `community.general.zypper` | SUSE package management |
| `community.general.apk` | Alpine package management |
| `community.general.pacman` | Arch Linux package management |
| `community.general.portage` | Gentoo package management |
| `community.general.pkgng` | FreeBSD package management |
| `community.general.timezone` | Timezone configuration |
| `community.general.locale_gen` | Locale generation |
| `community.general.htpasswd` | htpasswd files |
| `community.general.npm` | Node.js packages |
| `community.general.yarn` | Yarn packages |
| `community.general.pnpm` | pnpm packages |
| `community.general.cargo` | Rust packages |
| `community.general.nmcli` | NetworkManager connections |
| `community.general.filesystem` | Filesystem management |
| `community.general.parted` | Disk partitions |
| `community.general.lvg` | LVM volume groups |
| `community.general.lvol` | LVM logical volumes |

### community.docker

| Module | Description |
|--------|-------------|
| `community.docker.docker_container` | Manage containers |
| `community.docker.docker_container_exec` | Execute in container |
| `community.docker.docker_container_info` | Container information |
| `community.docker.docker_image` | Manage images |
| `community.docker.docker_image_build` | Build images |
| `community.docker.docker_image_info` | Image information |
| `community.docker.docker_image_pull` | Pull images |
| `community.docker.docker_image_push` | Push images |
| `community.docker.docker_network` | Manage networks |
| `community.docker.docker_network_info` | Network information |
| `community.docker.docker_volume` | Manage volumes |
| `community.docker.docker_volume_info` | Volume information |
| `community.docker.docker_compose_v2` | Docker Compose v2 |
| `community.docker.docker_login` | Registry authentication |
| `community.docker.docker_swarm` | Swarm management |
| `community.docker.docker_swarm_service` | Swarm services |
| `community.docker.docker_prune` | Prune unused objects |

### community.mysql

| Module | Description |
|--------|-------------|
| `community.mysql.mysql_db` | Manage databases |
| `community.mysql.mysql_user` | Manage users |
| `community.mysql.mysql_info` | Gather server information |
| `community.mysql.mysql_query` | Run queries |
| `community.mysql.mysql_replication` | Manage replication |
| `community.mysql.mysql_role` | Manage roles |
| `community.mysql.mysql_variables` | Manage variables |

### community.postgresql

| Module | Description |
|--------|-------------|
| `community.postgresql.postgresql_db` | Manage databases |
| `community.postgresql.postgresql_user` | Manage users/roles |
| `community.postgresql.postgresql_privs` | Manage privileges |
| `community.postgresql.postgresql_info` | Gather information |
| `community.postgresql.postgresql_query` | Run queries |
| `community.postgresql.postgresql_schema` | Manage schemas |
| `community.postgresql.postgresql_table` | Manage tables |
| `community.postgresql.postgresql_idx` | Manage indexes |
| `community.postgresql.postgresql_ext` | Manage extensions |
| `community.postgresql.postgresql_pg_hba` | Manage pg_hba rules |
| `community.postgresql.postgresql_subscription` | Manage subscriptions |
| `community.postgresql.postgresql_publication` | Manage publications |
| `community.postgresql.postgresql_slot` | Manage replication slots |

### kubernetes.core

| Module | Description |
|--------|-------------|
| `kubernetes.core.k8s` | Manage Kubernetes objects |
| `kubernetes.core.k8s_info` | Gather Kubernetes info |
| `kubernetes.core.k8s_scale` | Scale Kubernetes objects |
| `kubernetes.core.k8s_exec` | Execute in pods |
| `kubernetes.core.k8s_log` | Fetch pod logs |
| `kubernetes.core.helm` | Manage Helm charts |
| `kubernetes.core.helm_info` | Gather Helm info |
| `kubernetes.core.helm_repository` | Manage Helm repos |

## Ansible-Lint Rules Reference

| Rule ID | Description |
|---------|-------------|
| `fqcn` | Use FQCN for all modules |
| `fqcn[action-core]` | Use FQCN for builtin modules |
| `fqcn[canonical]` | Use canonical module names |
| `deprecated-module` | Avoid deprecated modules |
| `command-instead-of-module` | Use modules instead of shell commands |
| `command-instead-of-shell` | Use command instead of shell when possible |
| `no-free-form` | Avoid free-form command syntax |
| `risky-shell-pipe` | Check shell pipe safety |
| `package-latest` | Avoid `state: latest` in packages |

## Version Compatibility

| Ansible Version | Notes |
|-----------------|-------|
| 2.9 | Last version with modules in ansible core (pre-collections) |
| 2.10 | Collections architecture introduced |
| 2.11 | More modules migrated to collections |
| 2.12 | Many deprecated modules removed from core |
| 2.14 | FQCN strongly recommended, ansible.posix requires 2.15+ |
| 2.15+ | Canonical module names preferred for performance |
| 2.17+ | Latest stable, dnf5 module added |

## Resources

- [Ansible Collections Index](https://docs.ansible.com/ansible/latest/collections/index.html)
- [Ansible Porting Guides](https://docs.ansible.com/ansible/latest/porting_guides/porting_guides.html)
- [Ansible-Lint Rules](https://docs.ansible.com/projects/lint/rules/)
- [Ansible Galaxy](https://galaxy.ansible.com/)
