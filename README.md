# DevOps Skills for Claude

A collection of Claude skills dedicated to DevOps, designed to make the daily work of SREs (Site Reliability Engineers) easier.

## Description

This project brings together custom skills for Claude Code and OpenCode, enabling automation and acceleration of common DevOps tasks:

- Analysis and debugging of Kubernetes configurations
- Generation of manifests and templates
- Incident diagnosis and troubleshooting
- Log and metrics analysis
- Infrastructure as code management (Terraform, Ansible, etc.)
- Security best practices and compliance

The skills follow the open [Agent Skills](https://agentskills.io) standard, compatible with multiple AI tools.

## Available skills

WIP

## Installation

### Claude Code

#### From Plugin Marketplace (Recommended)

Add this repository as a Claude Code plugin marketplace and install the skills:

```bash
# Add the marketplace
/plugin marketplace add ddrugeon/devops-skills

# Install the plugin
/plugin install devops-skills@ddrugeon

```

#### Manually

**Global installation** (available in all your projects):

```bash
# Clone the repository
git clone https://github.com/ddrugeon/devops-skills.git

# Copy skills to your personal directory
cp -r devops-skills/skills-plugin/skills/* ~/.claude/skills/
```

**Per-project installation** (available only in a specific project):

```bash
# From your project root
cp -r devops-skills/skills-plugin/skills/* .claude/skills/
```

### OpenCode

OpenCode looks for skills in multiple locations, in order of priority:

1. `.opencode/skills/<name>/SKILL.md` (local project)
2. `~/.config/opencode/skills/<name>/SKILL.md` (global)
3. `.claude/skills/<name>/SKILL.md` (Claude compatible, local project)
4. `~/.claude/skills/<name>/SKILL.md` (Claude compatible, global)

**Global installation**:

```bash
# Option 1: OpenCode directory
cp -r devops-skills/skills-plugin/skills/* ~/.claude/skills/

# Option 2: Claude directory (compatible with both tools)
cp -r devops-skills/skills-plugin/skills/* .claude/skills/
```

**Per-project installation**:

```bash
# From your project root
cp -r /path/to/devops-skills/skills-plugin/skills/* .opencode/skills/
# or
cp -r /path/to/devops-skills/skills-plugin/skills/* .claude/skills/
```

## Usage

Once installed, skills can be:

- **Automatically invoked** by Claude when the context matches the description
- **Manually invoked** with `/skill-name` in Claude Code or OpenCode

## Contributing

Contributions are welcome. Feel free to open an issue or a pull request.

## License

This project is distributed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## References

- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [OpenCode Agent Skills Documentation](https://opencode.ai/docs/skills)
- [Agent Skills Standard](https://agentskills.io)
