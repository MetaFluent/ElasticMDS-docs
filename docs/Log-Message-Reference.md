# Log Message Reference

> **In preparation.** This catalog is being built out per component and grows over time.

When a deployment emits a `WARNING` or `SEVERE` log message, this page tells you what it means and what to do about it. It is a lookup, not a manual - go straight to the component that logged the message.

**Finding the component.** Every log record carries the **logger name** (the `ln` field - see [Operations: Logging](Operations-Logging.md)); that name identifies the component and matches a section below. `SEVERE` means system-down; `WARNING` means an error the system is operating through.

**Audience:** Operator (primary), Developer.

---

## How this catalog is organized

One section per component. Within each, a row per message the component can emit at `WARNING` or `SEVERE`:

| Column | Meaning |
|--------|---------|
| **Message** | The message text (or its stable pattern, with variable parts shown as `<...>`) |
| **Level** | `SEVERE` or `WARNING` |
| **Meaning** | What the condition is |
| **Action** | What an operator should do about it |

The messages originate in each component's `WARNING`/`SEVERE` log statements, so the catalog is refreshed by sweeping the components' sources - and a new component simply adds its own section.

---

## By component

### Content adapters

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-ADP-032` The relay has found no tables at its source cluster &lt;address&gt; after waiting &lt;seconds&gt; seconds (the last poll &lt;lastPoll&gt;); it relays nothing yet and keeps waiting. Check that the source cluster's gateway at &lt;address&gt; and its projectors are running and serving tables. | `WARNING` | Once its session to the source cluster is up, the relay waits for the source's tables before it starts relaying. Its polls of the source have returned no tables, or failed, for another warning interval. It keeps polling with no time limit, repeats this warning after each further interval, and starts relaying by itself when the first table appears; no restart is needed. | Check that the source cluster is up and publishing tables: its gateway at the named address is running and reachable from this node, and its projectors are running with their tables set up. The detail lines under the same code name what the last poll asked and its answer or failure. |
| `MF-ADP-035` Table &lt;table&gt; has waited &lt;seconds&gt; seconds for its table metadata from the node that owns the table and does not serve yet; it keeps waiting. Check that the table is running on the node that owns it and that the nodes are connected. | `WARNING` | A table that another node owns has not received that node's table metadata, so it cannot serve. In normal running the wait lasts only as long as the metadata takes to reach this node. A longer wait means the metadata was published and has not reached this node, this node defines a table the owning node does not publish, or the owning node or its table is not running. The table keeps waiting with no time limit, repeats this warning after each further interval, and starts serving by itself when the metadata arrives; no restart is needed. | Check that the table is running on the node that owns it, that this node defines only tables the owning node publishes, and that the nodes are connected. The detail lines that carry the same code name the table and how long it has waited. |

### Distribution servers

The push, refresh, pub-sub and relational servers that serve clients.

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-IO-014` The &lt;protocol&gt; server has waited &lt;seconds&gt; seconds for its authentication controller &lt;domain&gt; and does not serve yet: its network is held down, so clients cannot connect. It keeps waiting. Check that the authentication service for &lt;domain&gt; is deployed and running on this cluster, and the authentication domain name in the configuration. | `WARNING` | A server that validates its clients' sessions cannot work without its authentication controller, so it brings its network up only once the controller is available. In normal running the wait lasts only as long as the controller takes to start. A longer wait means the authentication service is not deployed or not running, or the server is configured with a domain name the service does not register. The server keeps waiting with no time limit, repeats this alert after each further interval, and starts by itself when the controller appears; no restart is needed. | Check that the authentication service for the named domain is deployed and running on this cluster, and that the authentication domain name in the server's configuration matches it. The detail lines that carry the same code name the server and how long it has waited. |
| `MF-IO-015` The &lt;protocol&gt; server could not resolve its authentication controller &lt;domain&gt; (&lt;reason&gt;), so it does not start its network and clients cannot connect. | `WARNING` | The lookup of the server's authentication controller in the security registry ended with a failure, or delivered no controller. The server stays held with its network down; it starts if the registry delivers the controller later. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry the failure. Restart the server once the cause is known. |
| `MF-IO-016` The &lt;protocol&gt; server received its authentication controller &lt;domain&gt; but could not start (&lt;reason&gt;), so clients cannot connect. | `WARNING` | The server was held waiting for its authentication controller. The controller arrived, but bringing the server up after it failed, so the server serves nothing. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry the failure. Restart the server. |
| `MF-IO-017` The &lt;protocol&gt; server could not set up its shared data in the cluster (&lt;reason&gt;), so it is not offered for use and serves nothing. | `WARNING` | While the server was starting, the shared cluster data it needs (its entry with the orchestration, its shard bindings, its routing records) could not be established. The server withdrew what it had already published, is not registered with its projector, and stays in an initialization error state. | Report it to MetaFluent support with the log around the message; the detail lines that follow it name the server, the data scope and the failure. Restart the server once the cause is known. |
| `MF-IO-018` The &lt;protocol&gt; server's network came up but the server could not publish its connection details to the cluster (&lt;reason&gt;), so clients are not routed to it. | `WARNING` | After the server's network came up, the record that tells clients and the orchestration where to connect could not be written to the cluster data. The server withdrew any record it had already published and reports its network as failed, so it serves no clients. | Report it to MetaFluent support with the log around the message; the detail line that follows it names the server and the failure. Restart the server once the cause is known. |
| `MF-IO-019` The &lt;protocol&gt; server could not serve a shard it was given, so clients cannot reach that shard on this server. Other shards are not affected. | `WARNING` | The server was assigned a shard but could not publish the record that tells clients where to connect for it (for example the user's session could not be looked up, or the cluster data could not be written). Each such shard is lost to its client; the server and its other shards keep running. The alert is raised once while the failures last for this server, and repeats within a minute are counted, not logged. | Report it to MetaFluent support with the log around the message; the detail line that follows it names the first shard and the failure, and the repeat summaries give the number of shards affected. |

### Refresh server

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-RFR-006` A client sent the refresh server a second connection request on a connection it had already opened, and the request was refused. | `WARNING` | A client sent a connection request on a refresh connection that already had one. The MetaFluent client library sends one per connection, so the client does not follow the protocol. The second request is refused and the connection carries on as it was opened. | Report it to MetaFluent support with the client application and its version, and the log around the message; the detail line that follows it names the connection and its session. |

### Query server

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-QRY-118` A client's query was refused because the query server could not answer its analysis. | `WARNING` | The query was analysed, but the result of that analysis was incomplete (for example it described no result columns), so the query server serving the client's connection could not answer it and the client was told the query is refused. A repeat of the query is analysed again. | Report it to MetaFluent support with the log around the message; support needs the detail lines that follow it. |

### Data fabric

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-FAB-015` This node cannot connect to the cluster node &lt;peer&gt; and keeps trying. Check that the node is running and that this node can reach it on the network. | `WARNING` | The node found another cluster node but could not open a connection to it, so it holds no copy of that node's data and shares none with it. The node tries again at its reconnect interval and the connection forms as soon as the other node answers. The state of this node is not changed. | Check that the named node is running and has finished starting, that its address and mesh port are reachable from this host, and that both nodes use the same mesh TLS settings. The detail lines give the cause of the latest attempt. |

> Sections are added as they are catalogued. Template for a new component:

### Client libraries

These messages are written to the application's own log by the MetaFluent client library it uses (JDBC, JMS), not by a server.

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-RFR-007` A client has not reconnected to the relational query server &lt;server&gt; for &lt;seconds&gt; seconds, so changes to where its query results are served, and the moves of their rows, are held up. Check that the relational query server is running and that the client can reach it. | `WARNING` | The client lost its connection to the relational query server and has been reconnecting since. Its query results keep updating over their own connections, but the client cannot learn where their rows move, so those moves wait for it. The client keeps reconnecting for as long as its session lasts and recovers its queries when it succeeds; this message is written once per outage. | Check that the relational query server is running and that the client can reach its address; the detail line that follows names the server, the attempts so far and the last failure. |
| `MF-PUB-019` A client has not reconnected to the pub-sub server &lt;server&gt; for &lt;seconds&gt; seconds, so its new subscriptions and publications wait, and changes to where its subscriptions are served are held up. Check that the pub-sub server is running and that the client can reach it. | `WARNING` | The client lost its connection to the pub-sub server and has been reconnecting since. Its subscriptions keep delivering over their own data connections, but the client cannot start new subscriptions or publications, or learn where its subscriptions move, until it reconnects. The client keeps reconnecting for as long as its session lasts and restores its subscriptions when it succeeds; this message is written once per outage. | Check that the pub-sub server is running and that the client can reach its address; the detail line that follows names the server, the attempts so far and the last failure. |

### &lt;Component name&gt; (`<logger name>`)

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| _(to be catalogued)_ | | | |

---

## Where to go next

- [Operations: Logging](Operations-Logging.md) - how to query these messages live.
- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom-to-remedy, which references this catalog.
