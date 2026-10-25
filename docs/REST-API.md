# REST API

The REST API is Elastic MDS's **control-plane** interface: it reads operational state and statistics from a running deployment, and controls a few runtime settings. REST is for **monitoring** a deployment and for **building tooling** around it.

For most operators, the **[Dashboard](Dashboard.md)** is the recommended way to watch a deployment - it presents these same signals in a browser, live, with no `curl`. This page is for when you want to query a deployment directly, script a check, or integrate it with your own monitoring.

**Audience:** operators; developers building monitoring or tooling.

The pages that use these calls - [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) and [Operations: Logging](Operations-Logging.md) - show the *what*; this page is the *how*: the grammar every one of those URLs is built from.

---

## The gateway

Every REST call goes to one place - the **API gateway**, which aggregates every component in the deployment behind a single host:

```
http://mf-api-gateway:9090
```

Plain HTTP on port `9090`. `mf-api-gateway` is a DNS name that must resolve to the gateway from wherever you run the command - see [Setting up a DNS entry for your API Gateway](Deployment-Basics.md#setting-up-a-dns-entry-for-your-api-gateway). (`localhost` does not reach it - the cluster runs behind the gateway alias.)

Calls are **read-mostly**: the great majority are `GET`s that change nothing. The few that mutate the running system are called out under [Controlling the running system](#controlling-the-running-system) below.

**Authentication.** The REST interface is authenticated with **API tokens** - present a `Bearer` token on each call (the examples in this wiki omit the header for brevity). Keep the gateway on a trusted network as well. See [Security: Basics](Security-Basics.md) and [API Token Administration](API-Token-Administration.md).

---

## The same services in every deployment

The gateway exposes the **same set of APIs in every deployment**, regardless of topology. A deployment is only a physical arrangement of one identical set of services, so what you learn here works unchanged from a single consolidated container to a large Kubernetes cluster. The only thing that differs between topologies is *which* container a given service runs in - and that is invisible from the gateway. A query you write against a laptop deployment runs untouched against production.

---

## Singletons and per-container APIs

Two kinds of API, and the difference decides how you address them:

- **Per-container APIs** have one instance per container (or per adapter) - for example `application-state`, `push-distribution-server`, `config`. You pick an instance with the segment right after `/v1/` (see [Addressing an instance](#addressing-an-instance)).
- **Singleton APIs** have exactly one instance in the whole deployment - for example `orchestration` and `log-service`. There is no instance to choose, so you address their resources directly, with no instance segment: `/api/orchestration/v1/sessions/...`.

The `apidoc` (below) tells you which an API is - its `info` block carries `x-singleton: true` or `false`.

---

## Discover what a deployment offers

The gateway describes itself - here is how to ask it what is available, rather than assuming a path.

**1. List the registered APIs.** The catalog names every API in the deployment:

```
curl -s "http://mf-api-gateway:9090/api/gateway/v1/apis/*/properties/name"
```

```json
["application-state","push-distribution-server","log-service","config","projector",
 "eta-client","session-server","orchestration","conflation-rules","log","gateway", ...]
```

**2. Read one API's `apidoc`.** Each API publishes an OpenAPI 3.0.3 document describing every path, verb, and field it exposes:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/apidoc"
```

Two things to read from it:

- **`paths`** - every resource and sub-resource the API offers, and the verbs on each. This is the authoritative list of what you can ask for; read it for the exact path, since each API's resources are its own.
- **`servers`** - the live **instances** of the API. Each entry is one instance's URL, and its `x-instance` value is that instance's id. This is where the real ids come from when you need to address one instance directly.

Every API answers at the fixed pattern `/api/<api-name>/v1/...`. The rest of this page is what goes after that.

---

## Addressing an instance

This section applies to **per-container** APIs. (Singletons have no instance segment - skip to [Working inside collections](#working-inside-collections).)

The segment after `.../v1/` chooses the instance. An instance id is usually a **UUID**; a few APIs use a readable **name** instead. The `apidoc` `servers` block lists the actual ids for the API you are querying.

**All instances - the wildcard `*`.** This is the form you will use most, and it copy-pastes as-is:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,role,state"
```
```json
[ { "name": "mf-mds-consolidated", "role": "ACTIVE", "state": "FULLY_OPERATIONAL" },
  { "name": "mf-eta-simulator",    "role": "ACTIVE", "state": "FULLY_OPERATIONAL" } ]
```

**One instance by id.** Substitute a real id from the `apidoc` `servers` block:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/<your-instance-id>/name,role,state"
```

**One (or several) instances by predicate.** A predicate is an `attribute operator value` test placed in the instance segment; it matches on any scalar field the resource exposes, not just its id. The predicate `name=mf-mds-consolidated` selects the instance whose name is exactly that:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/name=mf-mds-consolidated/name,role,state"
```

**Matching by substring - the `~` (like) operator.** Full names are tedious to type, so match on a fragment instead. The predicate `name~mf-mds` selects any instance whose name *contains* `mf-mds`:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/name~mf-mds/name,role,state"
```

A predicate that matches nothing returns an empty list, `[]` - so it filters as well as selects. The same mechanism picks out a broken component: the predicate `state=RECOVERING` returns only the containers currently recovering.

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/state=RECOVERING/name,info"
```

---

## Working inside collections

Many resources are **collections**, and collections can themselves contain collections - which is how you navigate several levels into a deployment with one URL.

The `orchestration` API shows the pattern well (and, being a singleton, needs no instance segment). Its nesting mirrors what a client is doing:

- a **session** is a connected client;
- each session holds one or more **statements** - the queries that client has open;
- each statement produces one or more **results**;
- each result is served by one or more **shards**.

That is four collections nested inside each other. Walk into them with `*` at each level. Ask every session for the text of every query it is running:

```
curl -s "http://mf-api-gateway:9090/api/orchestration/v1/sessions/*/statements/*/info/expression"
```
```json
[ "SELECT *, MFUtil.UPDATED(MFUtil.TIMER(250,'MILLISECONDS'),TRDPRC_1) AS CONSTRAINT_ FROM Chains.RDF WHERE ChainSymbol_='0#CHAIN.1000' AND CONSTRAINT_ = 1" ]
```

Go the whole way down - every shard's congestion level, across every result of every statement of every session:

```
curl -s "http://mf-api-gateway:9090/api/orchestration/v1/sessions/*/statements/*/results/*/shards/*/stats/concernLevel"
```

The nested arrays in the response mirror the nested collections in the path.

**Filter a collection by predicate.** The predicates from the previous section work at any level. Ask the push server for only the shards that are currently protecting a slow consumer - the predicate `autoConflationEngaged=true` keeps just those elements:

```
curl -s "http://mf-api-gateway:9090/api/push-distribution-server/v1/*/shards/autoConflationEngaged=true/shardID,offeredUpdates"
```

**Pick one element by name.** A bare name works for any name without a `/` in it, spaces and dots included:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/constituents/Memory%20Monitor/name,state"
```

**Names with grammar characters.** Some component names contain `=`, `[`, `]` (e.g. `PacketProtocolServer [protocol=SessionProtocol]`), which the selector grammar would otherwise try to interpret. The **literal-match** operator `name:value` takes the value verbatim:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/constituents/name:PacketProtocolServer%20%5Bprotocol=SessionProtocol%5D/name,state"
```

---

## Projection: shaping the response

By default a resource returns its whole object. Add a trailing field spec to get back only what you want - fewer bytes, and exactly the structure your script expects.

**One field:**

```
curl -s "http://mf-api-gateway:9090/api/log/v1/*/level"
```

**Several fields - a comma list** (one round trip, an object per instance):

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,role,state,info"
```

**A nested field - a dot-path token.** Reach into a sub-object without fetching the whole thing. The **verbatim dotted name is the JSON key** in the result (it is not re-nested):

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/*/name,system.summary.systemID"
```
```json
[ { "name": "mf-mds-consolidated", "system.summary.systemID": "0982160d-0c33-47da-91e0-218cb8777332" },
  { "name": "mf-eta-simulator",    "system.summary.systemID": "13ee295e-1f2f-4cc5-a855-1d6222f3baf3" } ]
```

A projection token that names nothing **fails loudly** - the response is an error naming the token, not a silent empty field - so a typo is easy to spot.

### Shallow vs deep

Whether nested collections are expanded is controlled by a **trailing slash**:

- **No trailing slash - shallow.** Nested collections are suppressed; you get the object's own fields.
- **Trailing slash - deep.** The gateway recurses into nested collections and returns them too.

```
curl -s "http://mf-api-gateway:9090/api/push-distribution-server/v1/*/shards/"   # deep: every shard, expanded
```

Reach for deep when you want a whole sub-tree in one call; stay shallow when you just want the top level.

---

## Controlling the running system

A few endpoints **change** the running deployment. These are the exception, and because they alter live behavior you should note the previous value and restore it when you are done.

The common one is **raising a component's log level** to investigate it - a `PATCH` on the `log` API:

```
curl -X PATCH "http://mf-api-gateway:9090/api/log/v1/<component>/level?level=FINE"
```

Set it back (usually `INFO` or `CONFIG`) once you have what you need. Retrieving log *records* is a separate, read-only API - see [Operations: Logging](Operations-Logging.md).

---

## Putting it together

The whole flow, end to end - discover, then query:

```
# 1. What APIs are here?
curl -s "http://mf-api-gateway:9090/api/gateway/v1/apis/*/properties/name"

# 2. What does the push server expose?
curl -s "http://mf-api-gateway:9090/api/push-distribution-server/v1/apidoc" | less

# 3. Ask a real question: which shards are protecting a slow consumer right now?
curl -s "http://mf-api-gateway:9090/api/push-distribution-server/v1/*/shards/autoConflationEngaged=true/shardID,offeredUpdates"
```

That last line reads as: on every push-distribution-server instance (`*`), take the `shards` collection, keep the elements where `autoConflationEngaged` is `true`, and return each one's `shardID` and `offeredUpdates`. Every URL on the Operations pages is assembled from exactly these pieces.

---

## Quick reference

| You want... | Form |
|-------------|------|
| List all APIs | `/api/gateway/v1/apis/*/properties/name` |
| Describe an API (and see if it is a singleton) | `/api/<api>/v1/apidoc` |
| A singleton API's resource | `/api/<api>/v1/<resource>` (no instance segment) |
| All instances | `/api/<api>/v1/*` |
| One instance by id | `/api/<api>/v1/<id>` |
| Instances where attribute equals | `/api/<api>/v1/<attr>=<value>` |
| Instances where attribute contains | `/api/<api>/v1/<attr>~<fragment>` |
| A collection element by name | `/.../collection/<name>` |
| ...name with special chars | `/.../collection/name:<verbatim value>` |
| Filter a collection | `/.../collection/<attr>=<value>` |
| One field | `/.../<id>/field` |
| Several fields | `/.../<id>/field1,field2` |
| A nested field | `/.../<id>/field,parent.child` |
| Expand nested collections | trailing `/` (deep) |
| Change a log level | `PATCH /api/log/v1/<id>/level?level=FINE` |

---

## Where to go next

- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - health, the broken constituent, and resource stats, built on these calls.
- [Operations: Logging](Operations-Logging.md) - querying the log service.
- [Dashboard](Dashboard.md) - the same signals in a browser (user guide to follow).
- [Glossary](Glossary.md) - definitions of the terms used here.
