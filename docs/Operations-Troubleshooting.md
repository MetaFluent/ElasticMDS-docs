# Operations: Troubleshooting & FAQ

This is the page to reach for when something is wrong. It is organized the way you actually work a problem: find the **symptom** that matches, look at the **likely cause**, and follow the **remedy**. It builds on [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) (is it healthy, which part, why) and [Operations: Logging](Operations-Logging.md) (what the component said); every check here is a read-only query to `mf-api-gateway:9090`.

**Audience:** Operator (primary), Developer.

> Prefer a screen? The **[Dashboard](Dashboard.md)** shows most of these signals live in a browser, and [AI-Assisted Troubleshooting](AI-Troubleshooting.md) is where this is heading - an assistant that runs the checks, captures the evidence, and analyzes it for you.

---

## Start here - what kind of trouble?

Jump to the closest match. If nothing quite fits, work the [standard diagnostic procedure](#standard-diagnostic-procedure) below.

**Startup and availability** - something will not come up
- [A component does not become operational](#startup-a-component-does-not-become-operational)
- [Cluster / standby questions](#cluster-and-redundancy)

**User (client) trouble** - an application cannot connect, or is not getting what it asked for
- [A client cannot connect](#connection-a-client-application-cannot-connect)
- [A client gets nothing, only status, or stale data](#client-data-a-client-gets-nothing-only-status-or-stale-data)

**Data trouble** - the content itself is missing, stale, or wrong
- [A source feed dropped, or a metadata mismatch](#source-data-an-adapter-cannot-get-or-encode-source-data)

**Performance** - slow or overloaded
- [A consumer lags, or a container is stressed](#load-and-overload)

---

## Standard diagnostic procedure

1. **Confirm the health first**, so you know which component and what state it is in:

   ```
   curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,role,state,info"
   ```

2. **Find the matching symptom** in the sections below and follow its likely cause and remedy.

3. **If the system was healthy and is now failing, capture the evidence *before* you restart.** A restart clears the very state that explains the failure - capturing first is the difference between a diagnosis and a guess:
   - Capture the full application state - state, constituents, and their history - over REST (see [Operations: Monitoring & Diagnostics](Operations-Monitoring.md)).
   - Where the deployment exposes them, pull a diagnostic (DataFabric) dump and export the recent log records from the log service (see [Operations: Logging](Operations-Logging.md)).
   - Open an issue with MetaFluent support and attach what you captured; note anything unusual about the timing.

   *(This capture-and-analyze step is exactly what [AI-Assisted Troubleshooting](AI-Troubleshooting.md) is being built to do for you.)*

---

## Startup: a component does not become operational

**Confirm:** read the state and reason, then drill into the stuck constituent and its history.

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,state,info"
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/constituents/*/name,state"
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/constituents/<name>/history"
```

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| Stuck at `INITIALIZING`, or terminal `INITIALIZATION_ERROR` | A required setting is missing or wrong (an unset `$(VAR)`, a bad host or path) | Check the effective configuration ([Configuration: Basics](Configuration-Basics.md)); correct the deployment's `deployment.properties`; restart the container |
| `INITIALIZING` never completes | A dependency the component needs (a source, store, or peer) is not up or not routable | The `info`/history reason names it - bring the dependency up or fix the address |
| `INITIALIZATION_ERROR` naming a file or resource | A file, descriptor, or mount the component expects is not present | Provide the resource the reason names; restart |
| A port/bind error in the logs | Another process holds the configured port | Free the port or reconfigure it; restart |

`INITIALIZATION_ERROR` is terminal - the component will not retry out of it. Fix the cause and restart.

---

## Cluster and redundancy

Redundant deployments run each protected service (session, pub/sub, SQL, orchestration) as an active/standby pair. **Before treating a standby as a problem, know what a healthy one looks like** - a hot standby is deliberately held short of fully operational.

**List the roles directly.** The predicate form gives you exactly the standbys, with their state and reason, in one call:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/role=STANDBY/name,role,state,info"
curl -s "http://mf-api-gateway:9090/api/application-state/v1/role=ACTIVE/name,role"
```

A **healthy** standby looks like this - `STANDBY`, `RESOURCE_COMPLETE`, "awaiting activation":

```json
[ { "name": "mf-session", "role": "STANDBY", "state": "RESOURCE_COMPLETE",
    "info": "PacketProtocolServer [protocol=SessionProtocol](self) -> RESOURCE_COMPLETE: Ready; awaiting activation" } ]
```

Redundant services appear as a same-named pair - one `ACTIVE`, one `STANDBY` - that share the `name` and are told apart by `system.summary.systemID`. (Note the projection quirk: a *lone* dotted token after a predicate returns `[]`; use the CSV form `.../role=STANDBY/name,system.summary.systemID`.)

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| A standby sits at `RESOURCE_COMPLETE` and never reaches `FULLY_OPERATIONAL` | **Normal** - a hot standby is held at `RESOURCE_COMPLETE`, awaiting activation | No action; it is ready and will take over if the active fails |
| A component you expect is absent from the state list or the catalog | Its container did not start, or cannot reach the gateway | Confirm the container is running ([Deployment: Basics](Deployment-Basics.md)); check gateway reachability (see the FAQ) |
| No instance shows `role` `ACTIVE` for a service that should have one | The active/standby members cannot see each other, so none has claimed the active role | Confirm the members are up and can reach one another over the control network; see active/standby in [Architecture: Advanced](Architecture-Advanced.md) |
| A standby did not promote after its active failed | The standby was not ready (`RESOURCE_COMPLETE`), or could not confirm the active was gone | Read the standby's state and history for the reason |

---

## Connection: a client application cannot connect

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| The connection times out | Wrong host or port | Client connects to the session server (e.g. `:8900`); verify the connection string ([JMS Application Development](Develop-JMS.md), [JDBC Application Development](Develop-JDBC.md)) |
| The connection is refused or nothing is listening | The server the client points at is not running, or is not reachable on the network | Confirm the target is up and routable |
| The connection is rejected with a context error | The named **context** is invalid or not loaded | Verify the context name the application selects ([JMS Application Development](Develop-JMS.md)) |
| The connection is rejected on login | Authentication or entitlement failure | Supply valid credentials; confirm the user is entitled ([Entitlements Context](Entitlements-Context.md)); login failures are logged server-side |

If your **REST** calls are what fail to connect (not a client app), that is a gateway/DNS issue - see the FAQ below.

---

## Source data: an adapter cannot get or encode source data

**Confirm:** find the adapter/constituent that is not fully operational and read its history and logs (see [Operations: Logging](Operations-Logging.md)).

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| A container rolls up to `RECOVERING`; its data goes stale | The upstream feed or connection went away (the source, the network path, or credentials) | The system reconnects on its own - confirm the source is reachable and watch for the return to `FULLY_OPERATIONAL`. `RECOVERING` is the system working, not a fault; it is a problem only if it does not clear |
| Warnings about fields or data conversion; specific content marked stale | The source metadata (data dictionary) does not match the data received | The affected content is marked stale so consumers are not misled; align the metadata/dictionary, or correct the publisher sending non-conforming data |

The history names the connection and the logs show the drop and retry - for the worked example (an ETA feed loss), see [Operations: Logging](Operations-Logging.md#worked-example-a-lost-feed).

---

## Client data: a client gets nothing, only status, or stale data

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| Subscribes successfully but receives no updates | Invalid topic/context syntax - the topic is *passive* (accepted but matches no content) | The context decides topic syntax; the bare v5 shorthand only works under the v5 context, while `MarketData-6.0.0` needs the schema-qualified form ([Dynamic Data Conventions](Dynamic-Data-Conventions.md)) |
| Receives only status messages, or "access denied" | Not entitled - the client, or the server on the client's behalf, is not permitted the content | Confirm the entitlement ([Entitlements Context](Entitlements-Context.md)); the status text carries the reason |
| Receives `STALE` | The upstream source is disrupted | This is the source-data case above - check the adapter's state |

---

## Load and overload

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| One client lags while others are fine | The client is a **slow consumer**; the system engaged auto-conflation to protect the others | Protective, not an error. Confirm with the shards query below; if chronic, the client must read faster or subscribe to less |
| A container is sluggish or reports `STRESSED` | CPU or memory pressure - too much subscribed content, an undersized container, or a runaway consumer | Add capacity, or let auto-scaling add a projector where it applies ([Architecture: Advanced](Architecture-Advanced.md)) |

```
curl -s "http://mf-api-gateway:9090/api/push-distribution-server/v1/*/shards/autoConflationEngaged=true/shardID,offeredUpdates"
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,system"
```

---

## FAQ

**What host do I use for REST calls?** `http://mf-api-gateway:9090`, always - never `localhost`. If a REST call cannot connect, the `mf-api-gateway` name is not resolving from your machine: set up the DNS entry ([Deployment: Basics](Deployment-Basics.md#setting-up-a-dns-entry-for-your-api-gateway)), and confirm the gateway container is up.

**Where are the logs?** Each component writes to its own log directory on disk, and the centralized log service answers queries across all of them at once ([Operations: Logging](Operations-Logging.md)).

**How do I turn up logging for one component?** `PATCH` its log level, and set it back when you are done ([REST API](REST-API.md#controlling-the-running-system)).

**Is `RECOVERING` an error?** No - the component lost a resource and is restoring it; it clears on its own. The only terminal states are `INITIALIZATION_ERROR` and `NON_FUNCTIONAL` ([Architecture: Basics](Architecture-Basics.md)).

**What does active/standby failover look like?** A standby is hot; on failover its `role` flips from `STANDBY` to `ACTIVE` in seconds and it takes over ([Architecture: Advanced](Architecture-Advanced.md)).

**It was working and now it is not - what do I do first?** Capture the evidence before you restart, per the [standard diagnostic procedure](#standard-diagnostic-procedure) above.

---

## Log message reference

For the meaning of a specific `WARNING` or `SEVERE` message and the recommended action, see the **[Log Message Reference](Log-Message-Reference.md)** - a per-component catalog of the messages a deployment can emit *(in preparation)*.

---

## Where to go next

- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - is it healthy, which part, and why.
- [Operations: Logging](Operations-Logging.md) - slicing the logs.
- [AI-Assisted Troubleshooting](AI-Troubleshooting.md) - the assistant that runs these checks for you *(preview)*.
- [Glossary](Glossary.md) - definitions of the terms used here.
