# Molecule Rules (Tests)

Evaluate the presence and quality of Molecule tests.

## M1: Missing Tests (Warning)

No `molecule/` directory in the role.

Expected minimal structure:

```text
role/
└── molecule/
    └── default/
        ├── molecule.yml      # Molecule configuration
        ├── converge.yml      # Execution playbook
        └── verify.yml        # Verification tests
```

## M2: Incomplete molecule.yml (Warning)

Missing minimal Molecule configuration.

```yaml
# molecule/default/molecule.yml
dependency:
  name: galaxy

driver:
  name: docker  # or podman, vagrant, delegated

platforms:
  - name: instance
    image: ubuntu:22.04
    pre_build_image: true

provisioner:
  name: ansible
  inventory:
    host_vars:
      instance:
        ansible_user: root

verifier:
  name: ansible
```

## M3: No Multi-Platform Tests (Info)

Tests on a single platform while the role supports multiple OS.

```yaml
# ✅ Good - test multiple platforms
platforms:
  - name: ubuntu-22
    image: ubuntu:22.04
    pre_build_image: true

  - name: ubuntu-20
    image: ubuntu:20.04
    pre_build_image: true

  - name: debian-12
    image: debian:12
    pre_build_image: true

  - name: rocky-9
    image: rockylinux:9
    pre_build_image: true
```

## M4: Minimal converge.yml (Info)

The convergence playbook doesn't test configuration variants.

```yaml
# ❌ Bad - default configuration only
# molecule/default/converge.yml
- name: Converge
  hosts: all
  roles:
    - role: myrole

# ✅ Good - test with custom variables
- name: Converge
  hosts: all
  vars:
    myapp_port: 9090
    myapp_user: testuser
    myapp_config:
      debug: true
  roles:
    - role: myrole
```

## M5: Missing or Empty verify.yml (Warning)

No post-convergence verifications.

```yaml
# ✅ Good - molecule/default/verify.yml
- name: Verify
  hosts: all
  gather_facts: false
  tasks:
    - name: Check service is running
      ansible.builtin.service_facts:

    - name: Assert service is running
      ansible.builtin.assert:
        that:
          - ansible_facts.services['nginx.service'].state == 'running'
        fail_msg: "nginx service is not running"

    - name: Check port is listening
      ansible.builtin.wait_for:
        port: "{{ myapp_port | default(8080) }}"
        timeout: 5

    - name: Check config file exists
      ansible.builtin.stat:
        path: /etc/nginx/nginx.conf
      register: config_file

    - name: Assert config exists
      ansible.builtin.assert:
        that:
          - config_file.stat.exists
```

## M6: No Additional Scenarios (Info)

Only one `default` scenario when multiple configurations should be tested.

```text
molecule/
├── default/           # Standard configuration
│   ├── molecule.yml
│   ├── converge.yml
│   └── verify.yml
├── ha/                # High availability configuration
│   ├── molecule.yml
│   ├── converge.yml
│   └── verify.yml
└── upgrade/           # Upgrade test
    ├── molecule.yml
    ├── converge.yml
    └── verify.yml
```

## M7: No prepare.yml (Info)

Prerequisites not handled before convergence.

```yaml
# molecule/default/prepare.yml - prepare the environment
- name: Prepare
  hosts: all
  tasks:
    - name: Install prerequisites
      ansible.builtin.package:
        name:
          - python3
          - sudo
        state: present

    - name: Create required directories
      ansible.builtin.file:
        path: /opt/app
        state: directory
```

## M8: No side_effect.yml (Info)

No testing of side effects (restart, failover).

```yaml
# molecule/default/side_effect.yml
- name: Side Effect - Test service restart
  hosts: all
  tasks:
    - name: Restart service
      ansible.builtin.service:
        name: nginx
        state: restarted

    - name: Wait for service to be ready
      ansible.builtin.wait_for:
        port: 80
        delay: 2
        timeout: 30
```

## M9: No Idempotence Test (Warning)

Idempotence is not explicitly verified.

```yaml
# molecule/default/molecule.yml
provisioner:
  name: ansible
  playbooks:
    converge: converge.yml
    verify: verify.yml
  # Enable idempotence test
  options:
    diff: true

# The idempotence test is run with:
# molecule converge && molecule idempotence
```

## M10: Undeclared Test Dependencies (Warning)

Test collections/roles not listed.

```yaml
# molecule/default/requirements.yml
collections:
  - community.docker
  - ansible.posix

roles:
  - name: geerlingguy.docker
```
