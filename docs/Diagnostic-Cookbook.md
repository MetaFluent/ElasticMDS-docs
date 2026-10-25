# Diagnostic Cookbook

> **Live document.** This is a running collection of diagnostic recipes, added to as
> operations are found useful and vetted. It is not exhaustive and does not aim to be.
> Entries may carry little explanation - the value is a recorded, correct command for an
> operation that is easy to forget or easy to get wrong.

Task-keyed diagnostic operations: the exact command for a specific diagnostic action. Copy the entry, substitute the marked placeholders, run.

**Audience:** Operator, Developer.

**How to read:** Each entry is one task and the command that performs it. Commands target `bash` and the gateway convention host `mf-api-gateway:9090`. For the REST projection and selection grammar these commands use, see [REST API](REST-API.md); for symptom-driven diagnosis, see [Troubleshooting & FAQ](Operations-Troubleshooting.md).

## Tracing

A trace records the internal handling of sessions, statements, and orchestration for a running session server. You start a trace, list the active ones, renew or stop them, and read the output in the logs. Every trace stops by itself after a limited time, so detailed tracing stays affordable.

Trace operations are addressed to the session-server API. The `*` element reaches the active session server; standby servers do not expose this API.

### Start a trace

`trace` is required and takes a trace specification. All other parameters are optional selectors that narrow what the trace covers.

```
curl -X POST "http://mf-api-gateway:9090/api/session-server/v1/*/traces?trace=orchestration:SHARD_CONTENT_BINDING:VERBOSE,orchestration:REQUEST&user=alice&table=md.quotes.rdf&minutes=10"
```

The response is the new trace ID.

| Parameter | Meaning |
|---|---|
| `trace` | The trace specification (see below). Required. |
| `user`, `application`, `position` | Select the sessions to trace. |
| `table` | Narrow the trace to a table, as `catalog.schema.table`. |
| `key` | Narrow the trace to a key. |
| `component` | Select a component, such as a projector. |
| `minutes` | How long the trace runs (see [Durations](#durations)). |

### Trace specification

A specification is a comma-separated list of entries:

- `subsystem:CATEGORY` - the category at basic detail.
- `subsystem:CATEGORY:VERBOSE` - the category at verbose detail.
- `subsystem:*` or `subsystem:*:VERBOSE` - every category of a subsystem, at basic or verbose detail.

Names and levels are case-sensitive. An unknown name or level is rejected with a message that lists the valid ones. For example:

```
orchestration:SHARD_CONTENT_BINDING:VERBOSE,orchestration:REQUEST
```

The `orchestration` subsystem provides categories today, and further subsystems are added over time. To list the subsystems and categories, each with its cost (`LIGHT` or `PER_ITEM`), a description, and the duration limits:

```
curl http://mf-api-gateway:9090/api/session-server/v1/*/traceCategories
```

### Selecting what to trace

The `user`, `application`, and `position` fields select sessions; `table` and `key` narrow a trace to content; `component` selects a component such as a projector. Every field is optional, an omitted field matches everything, and matching is exact. Fields combine - for example, user `alice` on table `md.quotes.rdf`. When several traces match a session, all of them apply.

### Durations

Every trace runs for a limited time and then stops by itself. If you omit `minutes`, the trace runs for the default of its tier. A value above the tier maximum is rejected with the reason. The tier follows from what you ask for:

| Tier | What it covers | Default | Maximum |
|---|---|---|---|
| `LIGHT` | Only light categories at basic detail | 15 minutes | 60 minutes |
| `HEAVY_NARROW` | Any per-item category or verbose detail, with a user, table, or key | 5 minutes | 30 minutes |
| `HEAVY_BROAD` | Per-item or verbose detail with no user, table, or key | 2 minutes | 5 minutes |

The limits are settings in the session server's configuration: `server.traceLightDefaultMinutes`, `server.traceLightMaximumMinutes`, `server.traceHeavyNarrowDefaultMinutes`, `server.traceHeavyNarrowMaximumMinutes`, `server.traceHeavyBroadDefaultMinutes`, and `server.traceHeavyBroadMaximumMinutes`.

### See the active traces

```
curl http://mf-api-gateway:9090/api/session-server/v1/*/traces
```

Each entry shows its `traceID`, selector, `traceSpecification`, `tier`, `minutes`, `expiresAt` (UTC), and `remainingSeconds`.

### Renew a trace

To run a trace for its duration again, counted from now:

```
curl -X PATCH "http://mf-api-gateway:9090/api/session-server/v1/*/traces/<ID>/expiresAt?value=renew"
```

To run for a different duration, stop the trace and start a new one with the `minutes` you want.

### Stop a trace

Address the trace by its ID in the path - the ID returned when the trace was started, or one from the active-traces list. An unknown ID is rejected.

```
curl -X DELETE http://mf-api-gateway:9090/api/session-server/v1/*/traces/<ID>
```

### Read the trace output

Each trace line in the logs starts with the category and the full trace ID, followed by what is being traced:

```
TRACE [subsystem.CATEGORY] [traceID=<full trace ID>] ...
```

The log service collects a trace's records from every container. To read them, newest first:

```
curl "http://mf-api-gateway:9090/api/log-service/v1/queryLogs?traceID=<ID>&limit=200"
```

`since` (epoch milliseconds), `text` (a substring the line must contain), `limit`, and `block=true` (wait for the next records) work as they do for the other log queries. Each record has the full trace line as its message, plus the trace IDs, subsystem, category, and level as separate fields.

If any records were dropped, either because a container produced them faster than it could send them or because the trace reached the log service's limit, the first record in the results says how many and where.

By default the log service keeps a trace's records for 60 minutes after its last record, up to 10,000 records per trace and 50 traces at a time (settings `centralizedLogService.traceRetentionMinutes`, `centralizedLogService.maxTraceRecords`, and `centralizedLogService.maxTraces`). To see which traces it currently holds:

```
curl http://mf-api-gateway:9090/api/log-service/v1/traces
```

The same lines also appear in each container's own log, so you can search those for the trace ID too.

## Related pages
- [Monitoring & Diagnostics](Operations-Monitoring.md)
- [Troubleshooting & FAQ](Operations-Troubleshooting.md)
- [REST API](REST-API.md)
