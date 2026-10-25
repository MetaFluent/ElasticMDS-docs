# Diagnostic Cookbook

> **Live document.** This is a running collection of diagnostic recipes, added to as
> operations are found useful and vetted. It is not exhaustive and does not aim to be.
> Entries may carry little explanation - the value is a recorded, correct command for an
> operation that is easy to forget or easy to get wrong.

Task-keyed diagnostic operations: the exact command for a specific diagnostic action. Copy the entry, substitute the marked placeholders, run.

**Audience:** Operator, Developer.

**How to read:** Each entry is one task and the command that performs it. Commands target `bash` and the gateway convention host `mf-api-gateway:9090`. For the REST projection and selection grammar these commands use, see [REST API](REST-API.md); for symptom-driven diagnosis, see [Troubleshooting & FAQ](Operations-Troubleshooting.md).

## Tracing

A trace records the internal handling of sessions, statements, and orchestration for a running session server. A trace is created against the session server, listed while active, and deleted when no longer needed.

Trace operations are addressed to the session-server API. The `*` element addresses all session-server instances; substitute a specific server ID to target one.

### Add a trace

`trace` is required and takes a trace specification. `ALL` enables all categories.

```
curl -X POST http://mf-api-gateway:9090/api/session-server/v1/*/traces\?trace=ALL
```

The response is the new trace ID.

To list the valid trace-specification categories:

```
curl http://mf-api-gateway:9090/api/session-server/v1/*/traceSpecificationHelp
```

A trace can be scoped with the optional `user`, `application`, and `position` query parameters.

### See the active traces

```
curl http://mf-api-gateway:9090/api/session-server/v1/*/traces
```

Each entry lists its `traceID` and `traceSpecification`.

### Delete a trace

Address the trace by its ID in the path - the ID returned when the trace was created, or one from the active-traces list.

```
curl -X DELETE http://mf-api-gateway:9090/api/session-server/v1/*/traces/<ID>
```

## Related pages
- [Monitoring & Diagnostics](Operations-Monitoring.md)
- [Troubleshooting & FAQ](Operations-Troubleshooting.md)
- [REST API](REST-API.md)
