# Runbook Structure — Complete Markdown Template

This file defines the exact structure of the document to generate.
Adapt the content to the application and the analyzed template.

The generated document must be written entirely in **French**.

---

~~~~markdown
# Runbook — Monitoring {APP_NAME} avec Zabbix

## Prérequis

- Accès admin à l'interface Zabbix
- {APP_NAME} configuré avec métriques activées
- Port {PORT}/tcp accessible depuis le serveur Zabbix
- Template `{TEMPLATE_NAME}` importé dans Zabbix (fichier YAML fourni)

---

## Vue d'ensemble

```text
{APP_NAME} /metrics (:{PORT})
  |
  +-- HTTP Agent (master item, {SCRAPE_INTERVAL}) --> {master_key}
        |
        +-- Dependent items : {liste des groupes fonctionnels}
        +-- LLD {règle} --> trigger {severity} par {dimension} découverte
```

### Macros du template

| Macro | Valeur par défaut | Description |
|---|---|---|
| `{$APP.METRICS.HOST}` | `localhost` | Hôte du endpoint Prometheus |
| `{$APP.METRICS.PORT}` | `{PORT}` | Port du endpoint Prometheus |
| `{$APP.METRICS.SCHEME}` | `http` | Schéma (http ou https) |
| `{$APP.SCRAPE.INTERVAL}` | `60s` | Intervalle de scrape du master item |
| ... | ... | ... |

---

## 1. Import du template Zabbix

> ⚠️ Cette opération est à faire si le template n'existe pas encore.

**Navigation :** Data collection → Templates → Import (bouton en haut à droite)

1. Sélectionner le fichier `zbx_template_{appname}_7_0.yaml`
2. Cocher **Delete missing** si une version précédente existe déjà
3. Cliquer **Import** — le template `{TEMPLATE_NAME}` apparaît dans
   Data collection → Templates → Templates/Applications

> ⚠️ Si l'import échoue avec "unexpected tag", vérifier que la version du
> fichier YAML est bien `'7.0'` et qu'il ne contient pas de champ `date`.

---

## 2. Activer les métriques dans {APP_NAME}

### 2.1 Configuration

{Instructions spécifiques à l'application}

### 2.2 Vérification

```bash
curl http://localhost:{PORT}/metrics | head -20
```

Résultat attendu :

```text
# HELP {app}_build_info ...
# TYPE {app}_build_info gauge
{app}_build_info{version="..."} 1
```

---

## 3. Lier le template au host

**Navigation :** Data collection → Hosts → [hôte {APP_NAME}] → Templates

1. Cliquer sur le host qui exécute {APP_NAME}
2. Onglet **Templates** → taper `{APP_NAME}` dans le champ de recherche
3. Sélectionner `{TEMPLATE_NAME}` → **Update**
4. Si {APP_NAME} n'écoute pas sur `localhost:{PORT}`, ajuster les macros :
   onglet **Macros** → **Inherited and host macros** → modifier les valeurs

---

## 4. Items

Tous les items sont hérités du template.

### Tableau de synthèse des items

| # | Key | Type | Type info | Preprocessing |
|---|---|---|---|---|
| 0 | `{master_key}` | HTTP Agent | Text | Aucun (master item) |
| 1 | `{key}` | Dependent | {type} | {preprocessing} |
| ... | ... | ... | ... | ... |

---

### Item 0 — Master item

> ℹ️ Source de données brutes. Tous les dependent items en dépendent.
> **Créer en premier** ou vérifier qu'il est bien présent avant de tester les autres.

#### Onglet Item

| Champ | Valeur |
|---|---|
| **Name** | `{name}` |
| **Type** | `HTTP agent` |
| **Key** | `{key}` |
| **URL** | `{$APP.METRICS.SCHEME}://{$APP.METRICS.HOST}:{$APP.METRICS.PORT}/metrics` |
| **Request method** | `GET` |
| **Type of information** | `Text` |
| **Update interval** | `{$APP.SCRAPE.INTERVAL}` |
| **History storage period** | `1d` |

---

### Items {N}–{M} — {Groupe fonctionnel}

Tous sont de type **Dependent item**, master item : `{master_key}`.

#### Onglet Item (commun)

| Champ | Valeur |
|---|---|
| **Type** | `Dependent item` |
| **Master item** | `{master_name}` |
| **Update interval** | `0` |
| **History** | `{history}` |
| **Trends** | `{trends}` |

#### Onglet Preprocessing

| Item | Metric pattern | Fonction |
|---|---|---|
| `{key}` | `{metric_name}` | `value` |
| ... | ... | ... |

---

### Item {N} — {Nom item histogramme}

#### Onglet Item

| Champ | Valeur |
|---|---|
| **Name** | `{name}` |
| **Type** | `Dependent item` |
| **Key** | `{key}` |
| **Master item** | `{master_name}` |
| **Type of information** | `Numeric (float)` |
| **Units** | `s` |

#### Onglet Preprocessing

Step 1 : `JavaScript`

```javascript
var lines = value.split('\n');
var totalSum = 0;
var totalCount = 0;
for (var i = 0; i < lines.length; i++) {
  var line = lines[i];
  if (line.indexOf('#') === 0 || line.trim() === '') continue;
  if (line.indexOf('{metric}_sum') === 0) {
    var parts = line.split(' ');
    totalSum += parseFloat(parts[parts.length - 1]);
  }
  if (line.indexOf('{metric}_count') === 0) {
    var parts = line.split(' ');
    totalCount += parseFloat(parts[parts.length - 1]);
  }
}
if (totalCount === 0) return 0;
return totalSum / totalCount;
```

Step 2 : `Change per second`

---

### Items LLD — {Nom de la règle de découverte}

La règle `{lld_key}` parse `{source_metric}` et crée des items par
`{dimension}` découverte.

#### Règle LLD

| Champ | Valeur |
|---|---|
| **Name** | `{name}` |
| **Type** | `Dependent item` |
| **Key** | `{lld_key}` |
| **Master item** | `{master_name}` |
| **Lifetime** | `7d` |

Preprocessing Step 1 : `Prometheus to JSON` → `{source_metric}`

Preprocessing Step 2 : `JavaScript`

```javascript
var metrics = JSON.parse(value);
var seen = {};
var result = [];
metrics.forEach(function(m) {
  var val = (m.labels && m.labels.{label}) ? m.labels.{label} : 'unknown';
  if (!seen[val]) { seen[val] = true; result.push({'{#MACRO}': val}); }
});
return JSON.stringify(result);
```

**Item prototypes créés par `{dimension}` :**

| Key | Type info | Unité | Description |
|---|---|---|---|
| `{key}[{#MACRO}]` | Float | `req/s` | {description} |
| ... | ... | ... | ... |

---

## 5. Triggers

### Tableau de synthèse des triggers

| # | Nom | Sévérité | Condition |
|---|---|---|---|
| 1 | {nom} | DISASTER | nodata ou endpoint down |
| 2 | {nom} | WARNING | {condition} |
| ... | ... | ... | ... |

---

### Trigger 1 — {Nom}

| Champ | Valeur |
|---|---|
| **Name** | `{nom}` |
| **Severity** | `{severity}` |
| **Expression** | voir ci-dessous |
| **Description** | {description opérationnelle} |

```text
{expression}
```

**Causes probables :**

- {cause 1}
- {cause 2}

**Diagnostic :**

```bash
{commandes de diagnostic}
```

---

## 6. Vérification post-configuration

### 6.1 Contrôle des items

**Navigation :** Monitoring → Latest data → filtrer sur le host + tag `Application: {appname}`

| Item | Valeur attendue | Statut nominal |
|---|---|---|
| {master_name} | Texte Prometheus brut | Présent, > 1 KB |
| {item_name} | {expected_value} | {nominal_status} |
| ... | ... | ... |

### 6.2 Contrôle des triggers

**Navigation :** Monitoring → Problems → filtrer sur le host.
Tous les triggers doivent être en statut **OK** (aucun problème actif).

> ℹ️ Si des items LLD n'apparaissent pas, attendre le premier cycle de
> découverte (jusqu'à 5 min). Forcer via : Data collection → Discovery rules
> → [règle] → **Execute now**.

### 6.3 Test du trigger DISASTER

```bash
# 1. Arrêter {APP_NAME}
sudo systemctl stop {service_name}

# 2. Attendre {nodata_delay} minutes
# Monitoring → Problems → "{trigger_name}" doit apparaître en DISASTER

# 3. Redémarrer {APP_NAME}
sudo systemctl start {service_name}
# Le trigger doit repasser en OK dans la minute suivante
```

### 6.4 Troubleshooting

| Symptôme | Action |
|---|---|
| Item en rouge "not supported" | Vérifier le preprocessing : inspecter via Items → **Test** |
| LLD ne découvre rien | Vérifier la métrique source dans `curl http://localhost:{PORT}/metrics` |
| Items CALCULATED en erreur | Attendre 2–3 cycles de collecte (items source doivent avoir une valeur) |
| `nodata` trigger permanent | Vérifier accessibilité du port {PORT} et le pare-feu |
| Trigger sonne en continu sans cause | Ajuster le seuil via la macro correspondante au niveau du host |

---

## 7. Référence rapide

### Items

| # | Key | Type | Preprocessing |
|---|---|---|---|
| 0 | `{master_key}` | HTTP Agent | Aucun (master) |
| 1 | `{key}` | Dependent | {preprocessing_summary} |
| ... | ... | ... | ... |

### Triggers

| # | Trigger | Sévérité | Seuil / Condition |
|---|---|---|---|
| 1 | {nom} | DISASTER | {condition} |
| 2 | {nom} | WARNING | > `{macro}` (défaut : {valeur}) |
| ... | ... | ... | ... |

---

*Dernière mise à jour : {date}*
*Environnement : {contexte}*
~~~~
