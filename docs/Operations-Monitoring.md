# Operations: Monitoring & Diagnostics

When something looks wrong, the API gateway answers three questions fast: **is the system healthy, if not which part is broken, and why.** Every check on this page is a read-only HTTP query to `mf-api-gateway:9090` - the same commands work from any machine once the [gateway DNS entry](Deployment-Basics.md#setting-up-a-dns-entry-for-your-api-gateway) is in place.

> **Prefer a screen to a shell?** The **[Dashboard](Dashboard.md)** presents these same signals in a browser. It is built entirely on the REST APIs below - so it shows the same data, live, without the `curl`. *(Dashboard user guide to follow.)*

---

## Is the system healthy?

Ask every component for its role and state:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,role,state,info"
```

What "healthy" means depends on the component's **role**:

- An **`ACTIVE`** component - or one with no active/standby role, shown as `n/a` - should be `FULLY_OPERATIONAL`.
- A **`STANDBY`** component is healthy at **`RESOURCE_COMPLETE`**: it is hot and ready, deliberately holding back from serving until it is promoted. A standby is *not* `FULLY_OPERATIONAL`, and that is correct (see [active/standby](Architecture-Advanced.md#high-availability-activestandby)).

In a non-redundant deployment, every component is `FULLY_OPERATIONAL`, each `ACTIVE` or `n/a` as above - here, a Static MDS deployment with two feed-partitioned projectors:

```json
[
    { "name": "mf-api-gateway",         "role": "n/a",    "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-core-srvcs",          "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-projector-mds-bpipe", "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-projector-mds-other", "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-admin",               "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" }
]
```

A redundant deployment adds a `STANDBY` for each protected service, sitting at `RESOURCE_COMPLETE`:

```json
[
    { "name": "mf-session", "role": "ACTIVE",  "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-session", "role": "STANDBY", "state": "RESOURCE_COMPLETE", "info": "PacketProtocolServer [protocol=SessionProtocol](self) -> RESOURCE_COMPLETE: Ready; awaiting activation" }
]
```

So healthy is: every `ACTIVE`/`n/a` component `FULLY_OPERATIONAL`, and every `STANDBY` at `RESOURCE_COMPLETE`. Anything else is your signal to drill in.

---

## Which part is broken?

A container's state is a roll-up of its **constituents** - the servers and controllers inside it. When a container is not fully operational, list them and find the one that is not:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/constituents/*/name,state"
```

```json
[ { "name": "PacketProtocolServer [protocol=SessionProtocol]", "state": "FULLY_OPERATIONAL" },
   { "name": "Projector",                                       "state": "RECOVERING" },
   { "name": "Memory Monitor",                                  "state": "FULLY_OPERATIONAL" } ]
```

Here `Projector` is the one to chase; the rest are fine. Each `state` is one of:

| State | Meaning |
|-------|---------|
| `FULLY_OPERATIONAL` | working normally |
| `INITIALIZING` | still starting - acquiring resources or connections |
| `RESOURCE_COMPLETE` | resources ready; awaiting activation |
| `STRESSED` | degraded but still serving |
| `RECOVERING` | restoring a resource it lost |
| `INITIALIZATION_ERROR` | failed to start |
| `NON_FUNCTIONAL` | failed at runtime |

A container reports the **worst** of its constituents' states, so the roll-up is `FULLY_OPERATIONAL` only when every constituent is. Constituents can themselves contain constituents, so a broken one may be a level down - follow the same `/constituents` path into it. The lifecycle these states move through is shown in [Architecture: Basics](Architecture-Basics.md).

---

## Why? - the state history

Each container and constituent keeps a timestamped **state-history buffer** - the record of how it got to its current state. This is usually enough to point at the cause:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/constituents/Projector/history"
```

```
2026-07-16 10:33:18 RECOVERING          ETAConnection-eta-server-host:14002 -> RECOVERING: Reconnecting
2026-07-16 09:33:23 FULLY_OPERATIONAL   All constituents fully operational
2026-07-16 09:33:23 RESOURCE_COMPLETE   ETATableAdapter Default.Quotes.CurveInputs -> Waiting for projector state resolution
```

Each line is a timestamp, a state, and a reason, most recent first: the top line is the current state, the lines below show how it got there. Here `Projector` went from `FULLY_OPERATIONAL` to `RECOVERING` when its ETA feed dropped - the reason names exactly what happened. (Append any constituent's name to `.../constituents/<name>/history`.) Turning a cause into a fix is the job of [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md).

---

## Resource monitoring

Three resources - **CPU, memory, and throughput** - across three levels: **containers, servers, and shards.**

**Containers - CPU and memory.** Each container reports its host stats:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,system"
```

```json
[
  { "name": "mf-mds-consolidated",
    "system": {
      "summary": { "loadAverage": 1.44, "memoryUsedPercent": 69 },
      "details": { "cpuCount": 24, "osName": "Linux" },
      "stats":   { "memoryFree": 490384712, "memoryMax": 16793993216 } } }
]
```

`summary.loadAverage` and `summary.memoryUsedPercent` give load and memory pressure at a glance.

**Servers and shards - throughput.** The push distribution server reports per-shard delivery stats, and whether the system has had to protect a slow consumer:

```
curl -s "http://mf-api-gateway:9090/api/push-distribution-server/v1/*/shards/"
```

```json
[
  { "shardID": "b8a8282a-7f27-4ff5-a456-de572a586bb0",
    "offeredUpdates": 2300314,
    "conflationRuleApplied": true,
    "autoConflationEngaged": false,
    "clientProfile": { "smoothedMeanRate": 2004.77, "projectedMaxRateUpdatesPerSec": 125000 } }
]
```

`clientProfile.smoothedMeanRate` is the current delivery rate (updates per second) and `offeredUpdates` the running total; `conflationRuleApplied` tells you the session matched a conflation rule, and `autoConflationEngaged` tells you the system has actually engaged conflation to keep a slow consumer from holding the others back. (Each shard carries more - streams, dictionaries, orchestration stats; byte-level I/O lives on the channels.) The full stat surface is in the [REST API](REST-API.md) reference.

---

## Component versions

To confirm exactly which build of each component is deployed - after an upgrade, or to check that every container is on the same version - query the `osgi-bootstrap` API. Every component is an OSGi bundle with a `name`, a `version`, and a `state`; the `bundleName` parameter is a regex (`.*` for all).

**What is running in a container.** List every component and its version:

```
curl -s "http://mf-api-gateway:9090/api/osgi-bootstrap/v1/*/bundles?bundleName=.*"
```

```json
[[
  { "name": "com.metafluent.blueprint.rtc.session.server.tcpip", "version": "6.3.0", "state": "ACTIVE" },
  { "name": "com.metafluent.application.state",                  "version": "1.4.0", "state": "ACTIVE" }
]]
```

Each result set (one inner array) is one container. To pin to a single container, select it by its `systemID` - the same identity you use for logs and state, from application-state (`name` -> `system.summary.systemID`):

```
curl -s "http://mf-api-gateway:9090/api/osgi-bootstrap/v1/systemID=<systemID>/bundles?bundleName=.*"
```

**What version of a component is deployed system-wide.** Narrow `bundleName` to the component and let `*` sweep every container - so you can confirm they all match, or catch one that has drifted:

```
curl -s "http://mf-api-gateway:9090/api/osgi-bootstrap/v1/*/bundles?bundleName=com.metafluent.blueprint.rtc.session.server.tcpip"
```

```json
[ { "name": "com.metafluent.blueprint.rtc.session.server.tcpip", "version": "6.3.0", "state": "ACTIVE" } ]
```

If different containers report different versions for the same component, the deployment is not uniformly upgraded.

---

## Logs

Two ways in:

- **On disk.** Every component writes to its log directory - the same place the configuration reports land (see [Configuration: Basics](Configuration-Basics.md)).
- **Over the gateway**, where the deployment exposes the log service - ask for recent errors:

  ```
  curl -s "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?level=SEVERE&limit=20"
  ```

  On a healthy system that returns an empty list - `[]`. Widen the level to see records; each entry is one log line:

  ```json
  [
    { "l": "WARNING",
      "ln": "com.metafluent.blueprint.rtc.eta.server.tcpip",
      "m": "initChannel",
      "msg": "channel.ioctl() failed: channel not in active state",
      "sID": "34f1505a-560e-48c3-95bd-8d020889cb6e" }
  ]
  ```

  Filter with `logger`, `text`, `since`, and `limit`; results are newest-first. (`l` level, `ln` logger, `c` / `m` class / method, `sID` the reporting container.) For the full set of ways to slice the logs - by component, container, text, and severity - see [Operations: Logging](Operations-Logging.md).

To investigate a specific component, raise its log level - a change to a running system, so restore it when you are done:

```
curl -X PATCH "http://mf-api-gateway:9090/api/log/v1/<component>/level?level=FINE"
```

---

## Going deeper

- [Dashboard](Dashboard.md) - the same signals in a browser (user guide to follow).
- [REST API](REST-API.md) - the `apidoc`, field projection, and predicate selection used throughout this page.
- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom to cause to fix.
- [Glossary](Glossary.md) - definitions of the terms used here.
