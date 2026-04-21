# Template Structure — Zabbix 7.0 YAML

## Global structure

```yaml
zabbix_export:
  version: '7.0'
  template_groups:
    - uuid: <32-hex>
      name: Templates/Applications
  templates:
    - uuid: <32-hex>
      template: 'App by HTTP'           # internal identifier
      name: 'App by HTTP'              # name displayed in the UI
      description: |
        Template description.
        Endpoint: http://{$APP.METRICS.HOST}:{$APP.METRICS.PORT}/metrics
        Compatibility: Zabbix 7.0+
      groups:
        - name: Templates/Applications
        - name: Templates/Teralab
      items:
        # Master item + all dependent items
      tags:
        - tag: class
          value: software
        - tag: target
          value: appname
      macros:
        # All template macros
      valuemaps:
        # Optional: mappings 0/1 → HEALTHY/UNHEALTHY etc.

  triggers:
    # Cross-item triggers (involving multiple items)
    # E.g.: FD ratio = fds/fds.max * 100
```

---

## Master Item (HTTP_AGENT)

Always first in the `items:` list:

```yaml
- uuid: <32-hex>
  name: 'App: Raw metrics'
  type: HTTP_AGENT
  key: app.metrics.get
  delay: '{$APP.SCRAPE.INTERVAL}'
  history: 1d
  trends: '0'
  value_type: TEXT
  url: '{$APP.METRICS.SCHEME}://{$APP.METRICS.HOST}:{$APP.METRICS.PORT}/metrics'
  description: 'Raw scrape of the Prometheus endpoint. All other items are dependent.'
  tags:
    - tag: component
      value: monitoring
```

---

## Dependent Item — Simple gauge

```yaml
- uuid: <32-hex>
  name: 'App: Go goroutines'
  type: DEPENDENT
  key: app.go.goroutines
  delay: '0'                    # mandatory for DEPENDENT
  history: 7d
  trends: 90d
  # value_type omitted = UNSIGNED by default
  description: 'Number of active Go goroutines.'
  preprocessing:
    - type: PROMETHEUS_PATTERN
      parameters:
        - go_goroutines         # metric name
        - value                 # function: value, label, sum, avg, min, max
        - ''                    # label name (empty if function != label)
  master_item:
    key: app.metrics.get        # must match the master item key exactly
  tags:
    - tag: component
      value: runtime
  triggers:
    - uuid: <32-hex>
      expression: 'last(/App by HTTP/app.go.goroutines)>{$APP.GOROUTINES.WARN}'
      name: 'App: High goroutine count'
      priority: WARNING
      description: 'Goroutines above threshold.'
      manual_close: 'YES'
      tags:
        - tag: component
          value: runtime
```

---

## Dependent Item — Counter with rate

```yaml
- uuid: <32-hex>
  name: 'App: Requests total (rate)'
  type: DEPENDENT
  key: app.requests.total
  delay: '0'
  history: 31d
  trends: 365d
  value_type: FLOAT
  units: req/s
  description: 'Request rate per second.'
  preprocessing:
    - type: PROMETHEUS_TO_JSON
      parameters:
        - my_metric_requests_total
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
  master_item:
    key: app.metrics.get
  tags:
    - tag: component
      value: traffic
```

---

## Dependent Item — Histogram (average latency)

```yaml
- uuid: <32-hex>
  name: 'App: Request duration avg (seconds)'
  type: DEPENDENT
  key: app.duration.avg
  delay: '0'
  history: 31d
  trends: 365d
  value_type: FLOAT
  units: s
  description: 'Average latency computed from the Prometheus histogram.'
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
  master_item:
    key: app.metrics.get
  tags:
    - tag: component
      value: latency
  triggers:
    - uuid: <32-hex>
      expression: 'avg(/App by HTTP/app.duration.avg,5m)>{$APP.LATENCY.WARN}'
      name: 'App: High request latency'
      priority: AVERAGE
      description: 'Average latency above threshold.'
      manual_close: 'YES'
```

---

## Dependent Item — Text label (version)

```yaml
- uuid: <32-hex>
  name: 'App: Build info (version)'
  type: DEPENDENT
  key: app.build.info
  delay: '0'
  history: 31d
  trends: '0'
  value_type: CHAR
  description: 'Application version extracted from the version label.'
  preprocessing:
    - type: PROMETHEUS_PATTERN
      parameters:
        - app_build_info        # metric with label version=...
        - label                 # extract the value of a label
        - version               # label name
  master_item:
    key: app.metrics.get
  tags:
    - tag: component
      value: availability
  triggers:
    - uuid: <32-hex>
      expression: 'change(/App by HTTP/app.build.info)=1'
      name: 'App: Version changed'
      priority: INFO
      description: 'Version changed. Verify that the update was planned.'
      manual_close: 'YES'
```

---

## Cross-item trigger (root section)

For triggers involving multiple items (e.g. ratio):

```yaml
# At the root of zabbix_export, after templates:
triggers:
  - uuid: <32-hex>
    expression: 'nodata(/App by HTTP/app.metrics.get,5m)=1'
    name: 'App: Service unavailable'
    priority: DISASTER
    description: 'The /metrics endpoint has not responded for 5 minutes.'
    manual_close: 'YES'
    tags:
      - tag: component
        value: availability

  - uuid: <32-hex>
    expression: 'last(/App by HTTP/app.go.process.fds) / last(/App by HTTP/app.go.process.fds.max) * 100 > 80'
    name: 'App: File descriptor usage high (>80%)'
    priority: WARNING
    description: 'More than 80% of file descriptors are in use.'
    manual_close: 'YES'
```

---

## Macros

```yaml
macros:
  - macro: '{$APP.METRICS.HOST}'
    value: localhost
    description: 'Prometheus endpoint host'
  - macro: '{$APP.METRICS.PORT}'
    value: 'PORT'
    description: 'Prometheus endpoint port'
  - macro: '{$APP.METRICS.SCHEME}'
    value: http
    description: 'Scheme: http or https'
  - macro: '{$APP.SCRAPE.INTERVAL}'
    value: 60s
    description: 'Scrape interval'
  # Trigger thresholds (one macro per trigger)
  - macro: '{$APP.LATENCY.WARN}'
    value: '0.1'
    description: 'Latency threshold in seconds (100ms)'
  - macro: '{$APP.GOROUTINES.WARN}'
    value: '1000'
    description: 'Go goroutine threshold'
  - macro: '{$APP.HEAP.WARN}'
    value: '536870912'
    description: 'Go heap threshold in bytes (512 MiB)'
```

---

## Value Maps (optional)

To display labels on 0/1 values:

```yaml
# In the template (under macros:)
valuemaps:
  - uuid: <32-hex>
    name: 'App health status'
    mappings:
      - value: '0'
        newvalue: UNHEALTHY
      - value: '1'
        newvalue: HEALTHY

# In the item that uses it:
valuemap:
  name: 'App health status'
```

---

## Low Level Discovery (LLD) — for dynamic metrics

When instances are dynamic (servers, upstreams, DNS zones...):

```yaml
discovery_rules:
  - uuid: <32-hex>
    name: 'App: Zones discovery'
    type: DEPENDENT
    key: app.zones.discovery
    delay: '0'
    description: 'Automatic zone discovery.'
    item_prototypes:
      - uuid: <32-hex>
        name: 'App: [{#ZONE}] Requests (rate)'
        type: DEPENDENT
        key: 'app.zone.requests[{#ZONE}]'
        delay: '0'
        history: 31d
        trends: 365d
        value_type: FLOAT
        units: req/s
        preprocessing:
          - type: PROMETHEUS_TO_JSON
            parameters:
              - 'my_metric_total{zone="{#ZONE}"}'
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
        master_item:
          key: app.metrics.get
    master_item:
      key: app.metrics.get
    preprocessing:
      - type: PROMETHEUS_TO_JSON
        parameters:
          - my_metric_total
      - type: JAVASCRIPT
        parameters:
          - |
            var metrics = JSON.parse(value);
            var seen = {};
            var result = [];
            metrics.forEach(function(m) {
              var z = (m.labels && m.labels.zone) ? m.labels.zone : 'unknown';
              if (!seen[z]) { seen[z] = true; result.push({'{#ZONE}': z}); }
            });
            return JSON.stringify(result);
```

---

## Trigger priorities

| Zabbix priority | YAML constant | Usage |
|---|---|---|
| Not classified | `NOT_CLASSIFIED` | Debug/test |
| Info | `INFO` | Non-critical changes (version) |
| Warning | `WARNING` | Thresholds to monitor |
| Average | `AVERAGE` | Performance degradation |
| High | `HIGH` | Critical errors, panics |
| Disaster | `DISASTER` | Service unavailable |

---

## Final checklist before import

- [ ] `version: '7.0'` present
- [ ] All UUIDs are 32-char hex without dashes
- [ ] Master item of type `HTTP_AGENT` with `value_type: TEXT`
- [ ] All dependent items have `delay: '0'`
- [ ] All dependent items have `master_item.key` matching the master
- [ ] Counters (`_total`) have `CHANGE_PER_SECOND` as the last preprocessing step
- [ ] Histograms use custom JavaScript (not `PROMETHEUS_PATTERN`)
- [ ] Calculated items have no preprocessing
- [ ] All macros used in expressions are declared
- [ ] `nodata(5m)=1` trigger at DISASTER for availability
- [ ] File named `zbx_template_<app>_7_0.yaml`
