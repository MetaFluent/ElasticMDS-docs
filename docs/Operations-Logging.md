# Operations: Logging

Every component logs, and the **log service** lets you query those logs live over the gateway - by component, by container, by text, and by severity. It is the tool you reach for when you are chasing a problem across a running system. Every query here is a read-only HTTP request to `mf-api-gateway:9090`.

**Logging is centralized.** Components forward their log records to the log service, which holds them. Unlike most gateway APIs, a `queryLogs` request is satisfied by the log service **itself** - it is *not* routed out to the individual containers - so a single query searches across every component at once. The log service also writes a **consolidated log file** to its own log output directory: one merged log of the whole system, in addition to the per-component log directory each component keeps on disk.

The one-line "recent errors" check is in [Operations: Monitoring & Diagnostics](Operations-Monitoring.md); this page is the fuller set of ways to slice the logs.

**Audience:** Operator (primary), Developer.

> **Availability.** The log service is present where the deployment exposes it (it may be folded into an admin tier and absent from a bare consolidated launch). If `/api/log-service/...` returns nothing, fall back to the on-disk log directory.

---

## The two identifiers you filter on

Most queries filter by a **component type** or a **container**:

- A component **type** is its **logger name**, e.g. `com.metafluent.blueprint.rtc.content.adapter.eta`. The `logger` filter is an **exact** match on that name.
- A **container** is identified by its **systemID**. List name-to-systemID for the deployment:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,system.summary.systemID"
```

```json
[
  { "name": "mf-mds-consolidated", "system.summary.systemID": "9f9e8615-0ea8-483f-ada6-42c924860f7f" },
  { "name": "mf-eta-simulator",    "system.summary.systemID": "34f1505a-560e-48c3-95bd-8d020889cb6e" }
]
```

---

## Reading a record

Each result is one log record - a small JSON object. Its fields (results are newest-first):

| Field | Meaning |
|-------|---------|
| `l` | level - `SEVERE`, `WARNING`, `INFO`, `FINE`, ... |
| `ln` | logger name (the component type) |
| `c` / `m` | source class / method |
| `msg` | the log message |
| `sID` | systemID of the reporting container |
| `s` / `n` | timestamp (seconds / nanoseconds) |

---

## All logs for a component type

Filter by `logger`:

```
curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?logger=com.metafluent.blueprint.rtc.content.adapter.eta&limit=20"
```

```json
[
  { "ln": "com.metafluent.blueprint.rtc.content.adapter.eta",
    "c": "...ETAContentAdapter", "m": "handleConnectionDown", "l": "WARNING",
    "msg": "ETATableAdapter Default.Quotes.RDF marking relevant content stale because: ETA Connection ... SocketChannel.read returned -1 (end-of-stream)",
    "sID": "9f9e8615-0ea8-483f-ada6-42c924860f7f", "s": 1784215998, "n": 152928332 }
]
```

Because the logger name identifies the *type*, this returns that type's logs across **every** container it runs in.

---

## That type on a specific container

Add `systemID` to pin it to one container:

```
curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?logger=com.metafluent.blueprint.rtc.content.adapter.eta&systemID=9f9e8615-0ea8-483f-ada6-42c924860f7f&limit=20"
```

---

## All logs for a container

Drop the logger and filter on `systemID` alone:

```
curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?systemID=9f9e8615-0ea8-483f-ada6-42c924860f7f&limit=20"
```

---

## Filter by text

`text` matches log records whose message contains the substring:

```
curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?text=stale&limit=20"
```

---

## Filter by severity

`level` selects a severity (`SEVERE`, `WARNING`, `INFO`, `FINE`, ...):

```
curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?level=WARNING&limit=20"
```

On a healthy system `level=SEVERE` returns an empty list `[]` - no news is good news.

---

## Combining filters

All parameters combine (AND), so you can narrow hard - for example, only the ETA adapter's warnings on one container:

```
curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?logger=com.metafluent.blueprint.rtc.content.adapter.eta&systemID=9f9e8615-0ea8-483f-ada6-42c924860f7f&level=WARNING&limit=20"
```

The full parameter set: `logger`, `systemID`, `level`, `text`, `class`, `method`, `since` (millis), and `limit`. Results are newest-first.

---

## Worked example: a lost feed

When a source feed drops, it shows up in both state and logs. Say the ETA market-data feed goes away:

**In state**, the container rolls up to `RECOVERING`, and drilling in points at the reconnecting constituent (see [Operations: Monitoring & Diagnostics](Operations-Monitoring.md)):

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,state,info"
```
```json
[ { "name": "mf-mds-consolidated", "state": "RECOVERING",
    "info": "ETAConnection-eta-server-host:14002 -> RECOVERING: Reconnecting" } ]
```

**In the logs**, the adapter marks its content stale and starts retrying:

```
curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?logger=com.metafluent.blueprint.rtc.content.adapter.eta&limit=20"
```
```
WARNING  handleConnectionDown  ETATableAdapter Default.Quotes.RDF marking relevant content stale because: ETA Connection ... SocketChannel.read returned -1 (end-of-stream)
INFO     connect               Attempting to connect to server eta-server-host:14002 ...
```

State tells you *what* is wrong and *which part*; the logs tell you *why*, in the component's own words.

---

## Where to go next

- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - health, the broken constituent, and resource stats.
- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom to cause to fix.
- [REST API](REST-API.md) - the query grammar (projection, predicates, the apidoc).
- [Glossary](Glossary.md) - definitions of the terms used here.
