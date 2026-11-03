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

### Pub-sub server

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-PUB-001` A client's subscription request failed inside the server. | `WARNING` | The server failed internally while answering a client's subscription request. The client was refused. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-002` New clients may be unable to find the pub-sub server because its address could not be published in the data fabric. Check the data fabric health and the network between the nodes. | `WARNING` | The pub-sub server could not write or renew its address in the data fabric, so new clients may not find it. The server tries again at each renewal. | Check that the data fabric is reachable and accepts writes, and the network between the nodes. |
| `MF-PUB-003` The pub-sub server did not start and serves no clients. Check the data fabric and the content adapter configuration, then restart the node. | `WARNING` | The pub-sub server could not start because it could not track the content adapters, so no client can subscribe through this node. | Check the data fabric and the content adapter configuration for the cluster, then restart the node. |
| `MF-PUB-009` A client's subscription could not be started. | `WARNING` | The server failed internally while starting a client's subscription, so the subscription was abandoned. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-010` A leftover subscription record could not be removed from the data fabric. Check the data fabric health on the cluster. | `WARNING` | A subscription could not start, and the record the server kept for it could not be removed from the data fabric. | Check that the data fabric is reachable; the record expires, or can be removed, once the data fabric recovers. |
| `MF-PUB-011` The server could not read a client's subscription request from the data fabric. Check the data fabric health on the cluster. | `WARNING` | The server could not read a client's subscription request from the data fabric, so that subscription was not started. | Check that the data fabric is reachable and responsive; the client can submit the subscription again. |
| `MF-PUB-012` Logins may be refused because the authentication domain &lt;domain&gt; could not be reached. Check that the authentication domain is configured and running. | `WARNING` | The server could not reach the service of an authentication domain, so logins through that domain may be refused. | Check that the named authentication domain is configured and running. |
| `MF-PUB-015` The server could not send a message to a connected client of application &lt;application&gt;, so some of its subscriptions may not deliver data. | `WARNING` | The server failed to write a message to a client connection that was still open: where a subscription's data comes from, a change in a subscription's state, or the acknowledgement of a subscription. The subscriptions concerned may not deliver data until the client reconnects. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-016` After a client of application &lt;application&gt; reconnected, the server could not release the subscriptions the client no longer holds. | `WARNING` | When a client reconnects it states again the subscriptions it holds, and the server releases the rest. That release failed, so the server may keep serving subscriptions nobody uses until the client's session ends. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-017` The server could not set up a client's connection, so the client was refused. | `WARNING` | A client connected to the pub-sub server with a valid session, and the server failed while setting up what it holds for that session. The client was refused and its connection closed; the client may connect again. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |

### Query server

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-QRY-118` A client's query was refused because the query server could not answer its analysis. | `WARNING` | The query was analysed, but the result of that analysis was incomplete (for example it described no result columns), so the query server serving the client's connection could not answer it and the client was told the query is refused. A repeat of the query is analysed again. | Report it to MetaFluent support with the log around the message; support needs the detail lines that follow it. |

### Data fabric

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-FAB-015` This node cannot connect to the cluster node &lt;peer&gt; and keeps trying. Check that the node is running and that this node can reach it on the network. | `WARNING` | The node found another cluster node but could not open a connection to it, so it holds no copy of that node's data and shares none with it. The node tries again at its reconnect interval and the connection forms as soon as the other node answers. The state of this node is not changed. | Check that the named node is running and has finished starting, that its address and mesh port are reachable from this host, and that both nodes use the same mesh TLS settings. The detail lines give the cause of the latest attempt. |

### Client libraries

These messages are written to the application's own log by the MetaFluent client library it uses (JDBC, JMS), not by a server.

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-PUB-004` A subscription did not restart after the client reconnected and may not deliver data. | `WARNING` | After the client reconnected to the server, a subscription failed to restart and may not deliver data. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-005` The client failed while cleaning up after a connection attempt that did not succeed. | `WARNING` | A client's attempt to connect to the pub-sub server failed, and then the client also failed while cleaning up the attempt. | Report it to MetaFluent support with the log around the message, including the earlier message about the connection attempt that failed. |
| `MF-PUB-006` The client's network reader for its connection to the pub-sub server failed. Check the client machine's network and resources (open connections, memory). | `WARNING` | The part of the client that reads from its connection to the pub-sub server reported a failure, and may report it again. | Check the network path from this client machine to the server, and the client host's limits on open connections and memory. |
| `MF-PUB-007` The client's network reader for a data connection failed. Check the client machine's network and resources (open connections, memory). | `WARNING` | The part of the client that reads from a data connection reported a failure, and may report it again. | Check the network path from this client machine to the server, and the client host's limits on open connections and memory. |
| `MF-PUB-008` Acknowledgements to the server are failing, so some rows may stay on hold. Check the network connection from this client to the server. | `WARNING` | The client could not send the server the acknowledgements that complete moving rows between shards, and retries them. Until they succeed, some rows stay on hold. | Check the network connection from this client to the server named in the detail lines. |
| `MF-PUB-013` A message listener in your application failed while handling a message. Check the application's listener for topic &lt;topic&gt;. | `WARNING` | The message listener of your application threw an exception while handling a message from a topic. | Check the application's listener code for the named topic, and the exception in the detail lines. |
| `MF-PUB-014` A subscription's data could not be applied on the client and is marked stale. | `WARNING` | The client failed to apply data it received for a subscription, so that subscription's data is marked stale. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-018` The client could not read a message the server sent on a data connection, so the connection was closed and its subscriptions are marked stale until they are restored on a new connection. | `WARNING` | The client received a message on a data connection that it could not read: content it could not decode, or a message type it does not know. Every later message on that connection would be lost, so the connection is closed; its subscriptions are marked stale and restored on a new connection. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |

> Sections are added as they are catalogued. Template for a new component:

### &lt;Component name&gt; (`<logger name>`)

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| _(to be catalogued)_ | | | |

---

## Where to go next

- [Operations: Logging](Operations-Logging.md) - how to query these messages live.
- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom-to-remedy, which references this catalog.
