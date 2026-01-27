# Role Structure Rules

Evaluate compliance with the standard Ansible Galaxy structure.

## S1: Missing Files (Warning)

Expected minimal structure:

```text
role/
├── README.md             # Recommended - role documentation
├── defaults/
│   └── main.yml          # Recommended - default variables (lowest precedence)
├── files/                # If static files are used
├── handlers/
│   └── main.yml          # If handlers are used
├── meta/
│   └── main.yml          # Recommended - role metadata, dependencies
├─── molecule/             # Molecule test scenarios if tests are used
│    └── default/
│        ├── molecule.yml
│        ├── converge.yml
│        └── verify.yml
├── tasks/
│   └── main.yml          # Required - main task list
│   ├── install.yml       # Installation tasks
│   └── configure.yml     # Configuration tasks
├── templates/            # If templates are used
└─── vars/
    └── main.yml          # Internal variables (non-overridable - higher precedence)
```

## S2: Missing or Incomplete README (Info)

A README should document:

```markdown
# Role Name

Role description.

## Requirements

Prerequisites (other roles, collections, Ansible versions).

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `app_port` | `8080` | Listening port |

## Dependencies

List of dependencies (Galaxy roles, collections).

## Example Playbook

\`\`\`yaml
- hosts: servers
  roles:
    - role: myrole
      vars:
        app_port: 9000
\`\`\`

## License

MIT

## Author Information

Author and contact.
```

## S3: Incomplete meta/main.yml (Warning)

Missing Galaxy metadata:

```yaml
# meta/main.yml
galaxy_info:
  author: your_name
  description: Role description
  license: MIT
  min_ansible_version: "2.14"

  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
    - name: Debian
      versions:
        - bullseye
        - bookworm

  galaxy_tags:
    - nginx
    - webserver

dependencies: []
```

## S4: License Not Specified (Info)

`meta/main.yml` should include a valid license:

```yaml
galaxy_info:
  license: MIT  # or GPL-3.0, Apache-2.0, BSD, proprietary
```

## S5: Undeclared Collections (Warning)

Using modules from collections without declaring them.

```yaml
# ❌ Bad - collection used but not declared
- community.general.ufw:
    rule: allow
    port: 22

# ✅ Good - declare in meta/main.yml or requirements.yml
# meta/main.yml
collections:
  - community.general

# or collections/requirements.yml
collections:
  - name: community.general
    version: ">=5.0.0"
```

## S6: Variable Organization (Info)

Poor distribution between `defaults/` and `vars/`:

| Directory | Usage | Override |
|-----------|-------|----------|
| `defaults/main.yml` | Default values, customizable by user | Yes |
| `vars/main.yml` | Internal variables, constants, calculations | Not recommended |
| `vars/*.yml` | Variables per OS/distribution | Loaded conditionally |

```yaml
# vars/Debian.yml - Debian-specific variables
nginx_package: nginx-full
nginx_service: nginx

# vars/RedHat.yml - RedHat-specific variables
nginx_package: nginx
nginx_service: nginx

# tasks/main.yml
- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"
```

**Comment out non-optional defaults** (Red Hat recommendation):

```yaml
# defaults/main.yml
# Variables with sensible defaults
myapp_port: 8080
myapp_user: appuser

# Required variables without meaningful defaults - commented out
# myapp_database_password:
# myapp_api_key:
# myapp_license_key:
```

This ensures all variables are discoverable in one place while making it clear which ones require user input.

## S7: Missing Argument Specifications (Info)

Role parameters not validated with `meta/argument_specs.yml`.

```yaml
# meta/argument_specs.yml
argument_specs:
  main:
    short_description: Configure and deploy MyApp
    description:
      - Installs and configures MyApp application
      - Supports multiple deployment modes
    author:
      - Your Name
    options:
      myapp_port:
        description: Port on which MyApp listens
        type: int
        default: 8080
      myapp_user:
        description: System user to run MyApp
        type: str
        default: appuser
      myapp_database_password:
        description: Database password (required)
        type: str
        required: true
        no_log: true
      myapp_deploy_mode:
        description: Deployment mode
        type: str
        default: standalone
        choices:
          - standalone
          - cluster
          - ha
      myapp_features:
        description: List of features to enable
        type: list
        elements: str
        default: []
```

**Benefits of argument specifications**:

- Validates parameters at role execution start
- Enables early failure detection with clear error messages
- Auto-generates role documentation
- Provides IDE/editor autocompletion support
