---
name: zabbix-template-generator
description: >
  Generates complete, importable Zabbix 7.0 YAML templates from Prometheus
  metrics exposed by an application. Use this skill whenever the user mentions:
  create a Zabbix template, monitor an application with Zabbix, generate a
  zbx_template_*.yaml file, export Prometheus metrics to Zabbix, or configure
  Zabbix items/triggers from a /metrics endpoint. The skill produces a YAML
  file directly importable into Zabbix via Data collection → Templates → Import.
version: 0.1.0
author: ddrugeon
tags: ["zabbix", "observability", "monitoring"]
---

# Zabbix Template Generator

Generates complete, importable Zabbix 7.0 templates from Prometheus metrics,
applying production-validated patterns.

## Workflow

### Step 1 — Collect source metrics

Ask the user to provide the raw content of the `/metrics` endpoint:

```bash
curl -s http://localhost:PORT/metrics
```

If the user cannot provide it, ask at minimum:

- The application name (e.g. CoreDNS, Caddy, etcd)
- The Prometheus endpoint port
- The key metrics to monitor

### Step 2 — Analyze metrics

Read `references/metric-patterns.md` to classify each metric and determine
the correct preprocessing strategy.

**Mandatory classification before generating:**

| Prometheus type | Zabbix strategy |
|---|---|
| `counter` (suffix `_total`) | `PROMETHEUS_TO_JSON` + JS sum + `CHANGE_PER_SECOND` |
| `gauge` | `PROMETHEUS_PATTERN` + `value` |
| `histogram` (_bucket/_sum/_count) | Custom JavaScript from raw stream |
| `summary` (quantile) | `PROMETHEUS_PATTERN` + label filter |
| label to extract | `PROMETHEUS_PATTERN` + `label` + label name |

### Step 3 — Generate the YAML template

Read `references/template-structure.md` for the exact YAML structure.

**Absolute rules:**

- UUIDs must be 32-char hex WITHOUT dashes (e.g. `e26e825b6e304bf0975a2ccec80222ae`)
- Generate a unique UUID per item, trigger, and group via `python3 -c "import uuid; print(uuid.uuid4().hex)"`
- The HTTP_AGENT master item must always be created first
- All dependent items reference the master via `master_item.key`
- Cross-item triggers go in the root `triggers:` section
- Single-item triggers go in `items[].triggers:`

### Step 4 — Validate and deliver

Check:

- [ ] All UUIDs are 32-char hex without dashes
- [ ] Master item exists with `type: HTTP_AGENT`
- [ ] Each dependent item has `delay: '0'` and `master_item.key`
- [ ] Counters (`_total`) have `CHANGE_PER_SECOND` as the last preprocessing step
- [ ] Histograms use custom JavaScript (not `PROMETHEUS_PATTERN`)
- [ ] Macros cover host, port, scheme, and all trigger thresholds
- [ ] File is named `zbx_template_<app>_7_0.yaml`

Save in the current directory and present with `present_files`.

---

## Critical production pitfalls

### 1. UUIDs — exact format

Zabbix 7.0 requires hex UUIDs with **32 characters and no dashes**.

- ✅ `e26e825b6e304bf0975a2ccec80222ae`
- ❌ `e26e825b-6e30-4bf0-975a-2ccec80222ae` (with dashes → import error)

Always generate via Python:

```bash
python3 -c "import uuid; print(uuid.uuid4().hex)"
```

### 2. Cumulative counters — always use `CHANGE_PER_SECOND`

`_total` metrics are counters that only ever increase.
Without `CHANGE_PER_SECOND`, graphs are unusable and triggers fire constantly.

Mandatory pipeline for a counter:

```yaml
preprocessing:
  - type: PROMETHEUS_TO_JSON
    parameters:
      - 'my_metric_total{label="value"}'
  - type: JAVASCRIPT
    parameters:
      - |
        var items = JSON.parse(value);
        var total = 0;
        items.forEach(function(m) { total += parseFloat(m.value); });
        return total;
  - type: CHANGE_PER_SECOND
    parameters:
      - ''
```

### 3. Histograms — JavaScript is mandatory, not PROMETHEUS_PATTERN

Prometheus histograms (`_bucket`, `_sum`, `_count`) have no `quantile` label.
`PROMETHEUS_PATTERN{quantile="0.99"}` returns "no data".

For average latency from a histogram:

```yaml
- type: JAVASCRIPT
  parameters:
    - |
      var lines = value.split('\n');
      var totalSum = 0;
      var totalCount = 0;
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (line.indexOf('#') === 0 || line.trim() === '') continue;
        if (line.indexOf('my_metric_seconds_sum') === 0) {
          var parts = line.split(' ');
          totalSum += parseFloat(parts[parts.length - 1]);
        }
        if (line.indexOf('my_metric_seconds_count') === 0) {
          var parts = line.split(' ');
          totalCount += parseFloat(parts[parts.length - 1]);
        }
      }
      if (totalCount === 0) return 0;
      return totalSum / totalCount;
- type: CHANGE_PER_SECOND
  parameters:
    - ''
```

**Do not** use a separate Calculated item (sum/count) — it creates division-by-zero
artifacts and produces aberrant values (minutes instead of milliseconds).

### 4. Multiple series — always aggregate with JavaScript

When a metric has multiple series (zones, servers, etc.),
`PROMETHEUS_PATTERN` with `sum` works, but label filtering combined with `sum`
can return "no data" if labels do not match exactly.

More robust strategy: `PROMETHEUS_TO_JSON` + JavaScript loop:

```yaml
- type: PROMETHEUS_TO_JSON
  parameters:
    - 'my_metric{rcode="NXDOMAIN"}'
- type: JAVASCRIPT
  parameters:
    - |
      var items = JSON.parse(value);
      var total = 0;
      items.forEach(function(m) { total += parseFloat(m.value); });
      return total;
```

### 5. Calculated item — no preprocessing

A `CALCULATED` item must have **no preprocessing steps**.
Its value is already the result of the formula. Adding a `PROMETHEUS_PATTERN`
on top causes the error "cannot parse metric name".

### 6. `CHANGE_PER_SECOND` on intermediate items of a Calculated

If you compute `sum/count` with two separate items + a Calculated, both source
items must have `CHANGE_PER_SECOND`. Otherwise the Calculated divides
cumulative counters that grow indefinitely → values in hours.
Prefer the all-in-one JavaScript solution (pitfall 3) to avoid this problem.

### 7. Absolute threshold triggers on counters

Never use `last(counter_total) > X` — the value only increases.
Use `avg(..., Nm) > X` after `CHANGE_PER_SECOND` to work on a rate.

---

## Item types to include systematically

For any application exposing Prometheus metrics:

**Availability (always include):**

- HTTP_AGENT master item → trigger `nodata(5m)=1` at DISASTER
- Version/build info → trigger `change()=1` at INFO

**Go runtime (if the app is written in Go):**

- `go_goroutines` → trigger high threshold at WARNING
- `go_memstats_heap_inuse_bytes` → trigger high threshold at WARNING
- `process_open_fds` + `process_max_fds` → trigger ratio >80% at WARNING

**Application metrics (depending on the app):**

- Request rate (counter → rate)
- Error rate (counter → rate) → trigger at HIGH
- Average latency (histogram → JS avg) → trigger at AVERAGE
- Panics/critical errors → trigger `change()>0` at HIGH

---

## Standard macros

Always include these macros in the template:

```yaml
macros:
  - macro: '{$APP.METRICS.HOST}'
    value: localhost
  - macro: '{$APP.METRICS.PORT}'
    value: 'PORT'
  - macro: '{$APP.METRICS.SCHEME}'
    value: http
  - macro: '{$APP.SCRAPE.INTERVAL}'
    value: 60s
  # + one macro per trigger threshold
```

---

## References

- `references/metric-patterns.md` — Detailed metric type classification and strategies
- `references/template-structure.md` — Complete YAML structure with annotated examples
