---
name: zabbix-runbook-generator
description: >
  Generates a complete operational Markdown runbook from a Zabbix YAML template
  (zbx_template_*.yaml). The runbook describes prerequisites, monitoring
  architecture, macros, import procedure, each item with its preprocessing,
  each trigger with its expression and resolution procedure, and a
  post-configuration verification section. Use this skill whenever the user
  mentions: generating documentation for a Zabbix template, creating a
  monitoring runbook, documenting Zabbix items/triggers, writing a template
  installation procedure, or produces a zbx_template_*.yaml file they want
  documented. The generated document is directly usable as a wiki page or
  runbook.
version: 0.1.0
author: ddrugeon
tags: ["zabbix", "observability", "monitoring", "runbook"]
---

# Zabbix Runbook Generator

Generates a complete operational Markdown runbook from a Zabbix 7.0 YAML
template.

> **Language rule:** The generated runbook document must be written in **French**.
> Only the file name uses English conventions (`runbook-zabbix-<appname>.md`).

## Input sources

The skill accepts one or more of the following sources:

1. **YAML file** — the `zbx_template_*.yaml` template (primary source)
2. **Raw metrics** — output of `curl /metrics` to enrich item descriptions
3. **Application context** — app name, port, architecture (if known)

If only the YAML is provided, generate the runbook from the YAML alone.
If raw metrics are also available, enrich the item descriptions.

## Workflow

### Step 1 — Parse the YAML template

Extract from the YAML:

- Template name (`template:`)
- Macros and their default values
- All items (master + dependent + LLD)
- All triggers (inline in items + root section)
- Value maps if any
- Template tags

### Step 2 — Reconstruct the architecture

Identify and describe the collection pattern:

```text
App /metrics (PORT)
  |
  +-- HTTP Agent (master item, {SCRAPE_INTERVAL})
        |
        +-- Dependent items : [list by functional group]
        +-- LLD rules : [list discovery rules]
              +-- Item prototypes
              +-- Trigger prototypes
  |
  +-- [Other HTTP Agents if present, e.g. separate availability check]
```

### Step 3 — Generate the Markdown document

Produce the document following the structure defined in `references/runbook-structure.md`.

**Writing rules:**

- All metric names, keys, and macros in `inline code`
- Trigger expressions in code blocks
- Tables for summaries (items, triggers, macros)
- Step-by-step procedures as numbered lists
- Bash commands in code blocks with `bash` language
- Adapt the level of detail: more verbose for complex items (LLD, Calculated)

### Step 4 — Enrich trigger descriptions

For each trigger, generate an operational description that includes:

- What the condition means concretely
- Probable causes
- Diagnostic commands to run
- Common corrective actions

Read `references/trigger-description.md` for description patterns by trigger
type.

### Step 5 — Save and present

- Name the file `runbook-zabbix-<appname>.md`
- Save in `/mnt/user-data/outputs/`
- Present with `present_files`

---

## Naming and style rules

### Mandatory sections in order

1. Prérequis
2. Vue d'ensemble (ASCII architecture diagram + macro table)
3. Import du template
4. Activation des métriques côté application
5. Liaison du template au host
6. Items (summary table + detail per item/group)
7. Triggers (summary table + detail per trigger)
8. Vérification post-configuration
9. Référence rapide (summary tables)

### Item classification for grouping

Group items by `component` tag or functional logic:

| Group | Example metrics |
|---|---|
| Disponibilité | master item, status check, build_info |
| Trafic | requests_total, responses_total per rcode |
| Latence | duration histogram |
| Runtime Go | goroutines, heap, GC, FDs |
| Applicatif | app-specific metrics |
| LLD | discovery rules + item/trigger prototypes |

### Level of detail by item type

**Master item HTTP_AGENT** → full table (Name, Type, Key, URL, Method, Type of info, Update interval, History)

**Simple dependent item (gauge)** → Item tab table + Preprocessing table (metric, function, label name)

**Counter dependent item** → Item tab table + Preprocessing table with 3 steps (PROMETHEUS_TO_JSON, JavaScript, CHANGE_PER_SECOND)

**Histogram dependent item** → table + full JavaScript code block

**Calculated item** → table + formula in inline code

**LLD Rule** → table + discovery JavaScript in code block + item prototype details

---

## Special sections to always include

### "Activation des métriques" section

Infer from the template how to enable metrics on the application side.
Examples by detected app:

- **CoreDNS** → add `prometheus` to the Corefile
- **Caddy** → add `metrics` to the global Caddyfile block
- **etcd** → `--listen-metrics-urls` at startup
- **Unknown app** → generic section with curl verification command

Always include the verification command:

```bash
curl http://localhost:PORT/metrics | head -20
```

### "Vérification post-configuration" section

Always include:

1. Item control table with expected values
2. Trigger check (all OK)
3. DISASTER trigger test (stop/restart the service)
4. Troubleshooting table (symptom → action)

### Standard troubleshooting table

| Symptôme | Action |
|---|---|
| Item en rouge "not supported" | Inspecter via Items → Test |
| LLD ne découvre rien | Vérifier la métrique source dans `curl /metrics` |
| Items CALCULATED en erreur | Attendre 2–3 cycles de collecte |
| `nodata` trigger permanent | Vérifier accessibilité du endpoint et le pare-feu |

---

## References

- `references/runbook-structure.md` — Complete Markdown template with all sections
- `references/trigger-description.md` — Operational description patterns by trigger type
