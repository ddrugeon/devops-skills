# Trigger Descriptions — Operational Patterns

For each trigger, generate a description that combines:

1. What the condition means concretely
2. Probable causes (bullet list)
3. Diagnostic commands
4. Corrective actions

All description content must be written in **French**.

---

## Pattern: Service unavailable (DISASTER)

**Condition type:** `nodata(Nm)=1` or `last(status)<>200`

**Description template:**
> Le endpoint `/metrics` de {APP_NAME} ne répond plus depuis {N} minutes.
> {APP_NAME} est probablement arrêté ou le port {PORT} est inaccessible.

**Causes probables:**

- Processus {APP_NAME} arrêté ou crashé
- Port {PORT} bloqué par le pare-feu
- Problème réseau entre le serveur Zabbix et le host

**Diagnostic:**

```bash
sudo systemctl status {service}
sudo journalctl -u {service} -n 50
ss -tlnp | grep {PORT}
curl -v http://localhost:{PORT}/metrics
```

---

## Pattern: Go panic / application crash (HIGH)

**Condition type:** `change(counter)>0`

**Description template:**
> Un panic Go a été détecté dans {APP_NAME}. C'est un signal d'erreur critique
> indiquant un bug dans l'application ou une corruption mémoire.

**Causes probables:**

- Bug applicatif ou nil pointer exception
- Corruption mémoire
- Dépendance inaccessible provoquant un état inattendu

**Diagnostic:**

```bash
sudo journalctl -u {service} -n 100
# Chercher les lignes "panic:" dans les logs
sudo journalctl -u {service} | grep -i panic
```

---

## Pattern: High application error rate (HIGH/AVERAGE)

**Condition type:** `avg(error_rate, Nm)>THRESHOLD`

**Description template:**
> Taux d'erreurs {TYPE} supérieur à {SEUIL} req/s en moyenne sur {N} minutes.
> Cause probable : {dépendance} inaccessible ou surchargée.

**Causes probables:**

- Backend / base de données inaccessible
- Timeout sur les connexions aval
- Requêtes malformées (problème client)
- Saturation des ressources

**Diagnostic:**

```bash
# Vérifier les logs applicatifs
sudo journalctl -u {service} -n 100 | grep -i error

# Vérifier la dépendance (ex: PostgreSQL)
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Pattern: Abnormally high DNS rcode rate (WARNING)

**Condition type:** `avg(rcode_rate, 5m)>THRESHOLD`

**Description template:**
> Taux de réponses {RCODE} supérieur à {SEUIL} req/s en moyenne sur 5 minutes.

**For NXDOMAIN:**
> Causes possibles : enregistrement manquant dans la base DNS,
> misconfiguration client, scan DNS externe.
> Corréler avec les logs CoreDNS pour identifier les noms demandés.

**For SERVFAIL:**
> Cause probable : backend PostgreSQL inaccessible ou surchargé.
> Vérifier la connexion pgsql et les connexions actives PostgreSQL.

**Diagnostic:**

```bash
# Voir les requêtes en erreur dans les logs
sudo journalctl -u coredns -n 100 | grep SERVFAIL
sudo journalctl -u coredns -n 100 | grep NXDOMAIN

# Vérifier PostgreSQL si SERVFAIL
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Pattern: High latency (AVERAGE)

**Condition type:** `avg(latency_avg, Nm)>THRESHOLD`

**Description template:**
> Latence moyenne de résolution supérieure à {SEUIL}s sur {N} minutes.
> Valeurs de référence : < 5ms (optimal), 5–50ms (normal avec backend),
> > 100ms (dégradé).

**Causes probables:**

- Backend (PostgreSQL, upstream HTTP) lent ou surchargé
- Congestion réseau
- Ressources CPU/mémoire insuffisantes sur le host

**Diagnostic:**

```bash
# Vérifier la charge système
top -bn1 | head -20
iostat -x 1 3

# Vérifier PostgreSQL (si applicable)
sudo -u postgres psql -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '1 seconds';"
```

---

## Pattern: Abnormally low traffic (AVERAGE)

**Condition type:** `avg(requests_rate, 10m)<1`

**Description template:**
> Moins d'une requête par seconde depuis 10 minutes.
> Signale généralement une rupture dans la chaîne de routage :
> délégation DNS cassée, problème réseau, ou service non joignable.

**Causes probables:**

- Délégation DNS non effective (propagation en cours)
- Glue records manquants ou incorrects
- Pare-feu bloquant le port DNS (53/UDP ou 53/TCP)
- Service non démarré

**Diagnostic:**

```bash
# Vérifier que le service répond localement
dig SOA {zone} @localhost

# Vérifier la délégation publique
dig +trace {zone}

# Vérifier les glue records au niveau TLD
dig NS {zone} @a0.org.afilias-nst.info +additional
```

---

## Pattern: Go runtime — Goroutines (WARNING)

**Condition type:** `last(goroutines)>THRESHOLD`

**Description template:**
> Nombre de goroutines Go supérieur à {SEUIL}.
> Possible fuite de goroutines ou surcharge momentanée.
> Une croissance continue sans retour à la normale est critique.

**Diagnostic:**

```bash
# Vérifier la tendance (est-ce que ça monte en continu ?)
# Regarder le graphe Zabbix sur 24h
# Si croissance continue → fuite de goroutines → redémarrage nécessaire
sudo systemctl restart {service}
```

---

## Pattern: Go runtime — Heap memory (WARNING)

**Condition type:** `last(heap_inuse)>THRESHOLD`

**Description template:**
> Mémoire heap Go supérieure à {SEUIL} octets ({SEUIL_MB} MiB).
> Surveiller la tendance pour détecter une fuite mémoire progressive.

**Causes probables:**

- Fuite mémoire applicative
- Charge exceptionnellement élevée
- Seuil trop bas par rapport au dimensionnement normal

**Actions:**

- Ajuster le seuil via la macro `{$APP.HEAP.WARN}` si la valeur est normale pour la charge
- Si croissance continue : redémarrer le service et investiguer dans les logs

---

## Pattern: File descriptors (WARNING)

**Condition type:** `fds / fds_max * 100 > 80`

**Description template:**
> Le processus {APP_NAME} utilise plus de 80% de ses file descriptors disponibles.
> Risque d'erreur "too many open files" et de refus de connexion.

**Corrective actions:**

```bash
# Voir la limite actuelle
cat /proc/$(pidof {service})/limits | grep "open files"

# Augmenter la limite system
# Dans /etc/security/limits.conf :
# {user} soft nofile 65536
# {user} hard nofile 65536

# Ou via systemd (dans /etc/systemd/system/{service}.service) :
# [Service]
# LimitNOFILE=65536
sudo systemctl daemon-reload && sudo systemctl restart {service}
```

---

## Pattern: Upstream/backend unhealthy (HIGH)

**Condition type:** `last(healthy)=0`

**Description template:**
> L'upstream `{#UPSTREAM}` est marqué unhealthy.
> Toutes les requêtes routées vers cet upstream échouent immédiatement.

**Diagnostic:**

```bash
# Vérifier la connectivité vers l'upstream
curl -v {upstream_url}
# Vérifier l'état du service backend
sudo systemctl status {backend_service}
sudo journalctl -u {backend_service} -n 50
```

---

## Pattern: Version change (INFO)

**Condition type:** `change(build_info)=1`

**Description template:**
> La version de {APP_NAME} a changé.
> Vérifier que la mise à jour était planifiée et que le service fonctionne correctement.

**Actions:**

- Confirmer avec l'équipe infrastructure que la mise à jour était planifiée
- Vérifier les release notes de la nouvelle version
- Confirmer que tous les triggers sont en OK après mise à jour

---

## General description writing rules

1. **Start with a status sentence**: describe what is happening concretely
2. **Give reference values** when relevant (e.g. < 5ms is normal)
3. **List probable causes** in order of likelihood
4. **Provide precise commands** that can be copy-pasted as-is
5. **Mention correlations** with other metrics when useful
6. **Indicate adjustable macros** if the threshold may cause false positives

**To avoid:**

- Vague descriptions ("quelque chose ne va pas")
- Commands without context
- Identical descriptions for all triggers of the same severity
