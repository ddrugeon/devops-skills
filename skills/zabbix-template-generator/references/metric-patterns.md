# Metric Patterns — Classification and Zabbix Strategies

## Identify the type of a metric

```bash
# Look for the TYPE line in the Prometheus stream
curl -s http://localhost:PORT/metrics | grep "^# TYPE my_metric"
# → # TYPE my_metric counter
# → # TYPE my_metric gauge
# → # TYPE my_metric histogram
# → # TYPE my_metric summary
```

---

## Counter (`_total`)

**Characteristics:**

- Always increasing, reset to zero only on restart
- `_total` suffix by Prometheus convention
- Can have multiple series (multiple label combinations)

**Zabbix strategy:**

1. `PROMETHEUS_TO_JSON` to aggregate all series
2. JavaScript to sum values
3. `CHANGE_PER_SECOND` to compute a rate

```yaml
preprocessing:
  - type: PROMETHEUS_TO_JSON
    parameters:
      - 'my_metric_total'                    # no filter = all series
      # or with partial filter:
      - 'my_metric_total{rcode="NXDOMAIN"}'  # filter on a label
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
value_type: FLOAT
units: req/s   # or events/s, errors/s depending on context
```

**Associated triggers:**

- High rate: `avg(/TEMPLATE/key,5m)>THRESHOLD`
- Abnormally low rate: `avg(/TEMPLATE/key,10m)<1`

---

## Gauge

**Characteristics:**

- Instantaneous value, can go up and down
- No `_total`, no `_bucket`
- Examples: goroutines, heap memory, open FDs, active workers

**Zabbix strategy:**

- Single series: `PROMETHEUS_PATTERN` + `value`
- Multiple series: `PROMETHEUS_TO_JSON` + JS sum/max/avg

```yaml
# Single series
preprocessing:
  - type: PROMETHEUS_PATTERN
    parameters:
      - go_goroutines
      - value
      - ''

# Multiple series → aggregate
preprocessing:
  - type: PROMETHEUS_TO_JSON
    parameters:
      - my_gauge_metric
  - type: JAVASCRIPT
    parameters:
      - |
        var items = JSON.parse(value);
        var total = 0;
        items.forEach(function(m) { total += parseFloat(m.value); });
        return total;
value_type: FLOAT   # or INTEGER for integer values
```

**Associated triggers:**

- High threshold: `last(/TEMPLATE/key)>THRESHOLD`
- Ratio: `last(/TEMPLATE/key.used) / last(/TEMPLATE/key.max) * 100 > 80`

---

## Histogram (`_bucket`, `_sum`, `_count`)

**Characteristics:**

- Generates 3 metric families: `_bucket{le=...}`, `_sum`, `_count`
- NO `quantile` label → `PROMETHEUS_PATTERN{quantile="0.99"}` = error
- Examples: request durations, response sizes

**Zabbix strategy — Average latency/size (recommended):**

JavaScript that reads the raw stream directly and computes sum/count:

```yaml
preprocessing:
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
value_type: FLOAT
units: s   # or B for sizes
```

**Alternative strategy — read a specific bucket:**

To approximate a percentile (e.g. p99 = bucket covering 99% of requests):

```yaml
preprocessing:
  - type: PROMETHEUS_TO_JSON
    parameters:
      - 'my_metric_seconds_bucket{le="0.032"}'
  - type: JAVASCRIPT
    parameters:
      - |
        var items = JSON.parse(value);
        var total = 0;
        items.forEach(function(m) { total += parseFloat(m.value); });
        return total;
value_type: FLOAT
```

**To avoid:**

- Separate Calculated item (sum/count) → startup artifacts, values in hours
- `PROMETHEUS_PATTERN` with `sum` on `_sum` or `_count` then division → unstable

---

## Summary (quantile)

**Characteristics:**

- Exposes pre-computed quantiles with `quantile` label
- Less common than histograms in modern applications

**Zabbix strategy:**

```yaml
preprocessing:
  - type: PROMETHEUS_PATTERN
    parameters:
      - 'my_metric_seconds{quantile="0.99"}'
      - value
      - ''
value_type: FLOAT
units: s
```

---

## Label to extract as text value

**Typical use case:** version, revision, state

```yaml
preprocessing:
  - type: PROMETHEUS_PATTERN
    parameters:
      - coredns_build_info     # the metric
      - label                  # extract the value of a label
      - version                # label name to extract
value_type: CHAR
```

**Associated trigger:**

- Version change: `change(/TEMPLATE/key)=1` at INFO

---

## Go runtime metrics (common to all Go applications)

| Metric | Type | Suggested key | Units |
|---|---|---|---|
| `go_goroutines` | gauge | `app.go.goroutines` | — |
| `go_memstats_alloc_bytes` | gauge | `app.go.heap.alloc` | B |
| `go_memstats_heap_inuse_bytes` | gauge | `app.go.heap.inuse` | B |
| `process_open_fds` | gauge | `app.go.process.fds` | — |
| `process_max_fds` | gauge | `app.go.process.fds.max` | — |
| `go_gc_duration_seconds_sum` | histogram | `app.go.gc.duration` | s |

Standard Go triggers:

- Goroutines > threshold → WARNING
- Heap > threshold → WARNING
- Used FDs / Max FDs > 80% → WARNING (cross-item trigger in root section)

---

## Special cases

### Metric with ambiguous multiple series

If a metric has series per zone, server, view, etc. and you want the global
total → always use `PROMETHEUS_TO_JSON` + JS sum.

If you want to keep per-dimension granularity → use a Low Level Discovery
rule (see `template-structure.md` LLD section).

### Metric absent from the stream

If `curl /metrics | grep my_metric` returns nothing:

- Check that the plugin/middleware exposing it is enabled
- Check the exact name (may differ between versions)
- Preprocessing will return "no data" → item shown in red in Zabbix

### Boolean value (0/1)

```yaml
value_type: FLOAT  # or leave as default
# Add a valuemap to display HEALTHY/UNHEALTHY
valuemap:
  name: 'App health status'
```
