# Log Message Reference

> **In preparation.** This catalog is being built out per component and grows over time.

When a deployment emits a `WARNING` or `SEVERE` log message, this page tells you what it means and what to do about it. It is a lookup, not a manual - go straight to the component that logged the message.

**Finding the component.** Every log record carries the **logger name** (the `ln` field - see [Operations: Logging](Operations-Logging.md)); that name identifies the component and matches a section below. Every alert message also begins with its message ID, which names the component too. `SEVERE` means system-down; `WARNING` means an error the system is operating through.

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

Each message starts with its message ID (`MF-&lt;AREA&gt;-&lt;NNN&gt;`); search your logs for the ID. The text below shows variable parts as `<...>`.

### Network I/O

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-IO-010` The &lt;protocol&gt; server lost its network on port &lt;port&gt; (&lt;trigger&gt;), so clients cannot connect. It is trying to bring the network back every &lt;retryMillis&gt; ms. Check the machine's network interfaces and what else is using the port. | `WARNING` | The listener of a protocol server stopped, so the server released it and is retrying. The server reports the network up again in the log when a retry succeeds. The alert is raised once for each outage, not for each retry. | Check the state of the network interfaces and that no other program has taken the port (for example with ss -ltnp); the log line that follows names the failure in full. If the message is not followed by a line reporting the network up again, restart the server. |
| `MF-IO-011` The &lt;protocol&gt; server could not restart its network after losing it (&lt;reason&gt;), so clients cannot connect. It keeps trying every &lt;retryMillis&gt; ms. Check the machine's network interfaces, the configured address and port, and what else is using the port. | `WARNING` | After the server lost its network, a restart attempt failed. The server retries at the interval shown and reports the network up again in the log when a retry succeeds. The alert is raised once for the first failed retry of an outage, not for each retry; the server's restartFailures statistic counts them. | Check the network interfaces, the configured address and port, and that no other program has taken the port (for example with ss -ltnp); the log lines that follow name the failure in full. If no line reporting the network up again follows, restart the server. |
| `MF-IO-012` The &lt;protocol&gt; server could not start its network on port &lt;port&gt; (&lt;reason&gt;), so clients cannot connect. Check the machine's network interfaces, the configured address and port, and what else is using the port. | `WARNING` | When the server became the active one it could not open its network, so it released what it had started and serves nothing. This is the server's first start; a restart after the network was lost is reported by MF-IO-011. | Check the network interfaces, the configured address and port, and that no other program has taken the port (for example with ss -ltnp); the log lines that follow name the failure in full. Then restart the server. |

### Pub-sub

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-PUB-015` The server could not send a message to a connected client of application &lt;application&gt;, so some of its subscriptions may not deliver data. | `WARNING` | The server failed to write a message to a client connection that was still open: where a subscription's data comes from, a change in a subscription's state, or the acknowledgement of a subscription. The subscriptions concerned may not deliver data until the client reconnects. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-016` After a client of application &lt;application&gt; reconnected, the server could not release the subscriptions the client no longer holds. | `WARNING` | When a client reconnects it states again the subscriptions it holds, and the server releases the rest. That release failed, so the server may keep serving subscriptions nobody uses until the client's session ends. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |
| `MF-PUB-017` The server could not set up a client's connection, so the client was refused. | `WARNING` | A client connected to the pub-sub server with a valid session, and the server failed while setting up what it holds for that session. The client was refused and its connection closed; the client may connect again. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry what support needs. |

### Session server

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-SES-005` A client signing in was refused because of an internal failure. | `WARNING` | A client sent a sign-in that the session server failed to complete for a reason that is not the client's credentials or connection. The client is refused and retries. | Report it to MetaFluent support with the log around the message; the detail line that follows it carries the failure, the user and the position. |
| `MF-SES-006` Clients cannot sign in or resume their sessions because no query servers are registered with the session server. Check that the query servers (relational and pub-sub) are running and can reach the cluster. | `WARNING` | The session server holds no statement servers to offer clients, so every sign-in and session resume is refused until one registers. Clients retry. | Check that the query servers (relational and pub-sub) are deployed, running and joined to the cluster; once one registers, clients sign in again without intervention. |

### Push server

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-PSH-017` The server failed while &lt;activity&gt; for the data of &lt;key&gt;, so clients may be missing data or receive none for it. Later failures on the same data are counted, not logged. | `WARNING` | The server failed internally while building or sending data for one content stream. The same stream fails the same way every time, so the first failure is logged with the stream's shape and later ones are only counted. | Report it to MetaFluent support with the log around the message; the detail lines that follow it carry the stream's shape and the failure. The failure counts for the stream are on the push server's REST. |

### Content adapters

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-ADP-030` The connection to upstream provider &lt;endpoint&gt; is down; &lt;rows&gt; rows of &lt;tables&gt; tables are marked stale until it reconnects. Check the upstream provider &lt;endpoint&gt; and the network path to it. | `WARNING` | A connection of the ETA adapter to its upstream provider dropped, so the rows it carries are marked stale. The adapter reconnects and requests the rows again. | Check that the upstream provider is up and reachable from this node. The rows recover once the connection is back; the log says when each table starts recovering them. |
| `MF-ADP-031` The relay could not open its session to source cluster &lt;address&gt; within &lt;seconds&gt; seconds and relays nothing. Check that the source cluster's pub-sub service is running and reachable from this node, and the relay's credentials. | `WARNING` | At startup the relay (the compute tier's adapter for tables of another MetaFluent cluster) could not open its pub-sub session to its source cluster in time, so it relays no tables. | Check that the source cluster is running, that its pub-sub service is reachable from this node, and the relay's credentials; the detail lines under the same code name the last attempt's failure. Restart the relay's node once the source is available. |
| `MF-ADP-032` The relay found no tables at its source cluster &lt;address&gt; within &lt;seconds&gt; seconds (the last poll &lt;lastPoll&gt;) and relays nothing. Check that the source cluster is running and serves its tables, and the network path to its gateway. | `WARNING` | At startup the relay's polls of its source cluster for the tables to relay returned none, or failed, until the time allowed ran out, so it relays no tables. | Check that the source cluster is running with its tables set up, and that its gateway is reachable from this node; the detail lines under the same code name what the last poll asked and its answer or failure. Restart the relay's node once the source serves its tables. |
| `MF-ADP-033` Relayed table &lt;table&gt; is not set up: its source cluster &lt;address&gt; lists the table but offers no field dictionary for it. Check that the source cluster's adapter for the table is running. | `WARNING` | The source cluster lists a table, but no field dictionary for it is offered on its REST interface, so the relay cannot set the table up. The next discovery poll tries again. | Check that the adapter serving the table in the source cluster is running and operational; the table is set up at the next poll once its dictionary is offered. |
| `MF-ADP-034` The field dictionary of relayed table &lt;table&gt; could not be read from source cluster &lt;address&gt;; the table is not set up. Check the network path to the source cluster's gateway and that the gateway is running. | `WARNING` | Reading a table's field dictionary from the source cluster's REST interface failed, so the relay cannot set the table up. The next discovery poll tries again. | Check the network path to the source cluster's gateway, that the gateway is running, and the relay's credentials; the detail lines under the same code name the request and its failure. |

### Orchestration

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-ORC-025` A row of table &lt;table&gt; lost its place on a shard and was not placed again, so it is no longer served. | `WARNING` | A row's binding to its shard ended while no remediation task was active to take the row, so nothing placed the row again. The row stays unserved until its query is re-run or the table is re-orchestrated. | Report it to MetaFluent support with the log around the message; give the table name and say what was happening to the table's projectors at the time. |

### Synthetic (computed) content

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-SYN-007` A computed row of table &lt;table&gt; failed and is shown as INVALID; later failing rows of the table are counted, not logged. | `WARNING` | A computed row could not be built or kept up to date for an internal reason, so its state is INVALID and its state text names the stage and the cause. The detail line names the first failing row; the table adapter's REST shows how many rows failed, by stage. | Report it to MetaFluent support with the log around the message; the detail lines under the same code and the query that uses the computed columns, if known, are needed. |
| `MF-SYN-008` Function library &lt;library&gt; became the primary on this node but could not take the role up; queries using its functions may not be answered. | `WARNING` | This node won the election for a function library but a step of taking the role up failed or could not run, so the library's queries may not be dispatched from this node. The detail line names the step that failed and the steps done before it; the library adapter's REST shows the takeover. | Report it to MetaFluent support with the log around the message; the detail lines under the same code are needed. |
| `MF-SYN-009` Some rows of a &lt;statementKind&gt; query could not be read or combined on this node, so its groups may be incomplete; later failures of the query are counted, not logged. | `WARNING` | The part of a grouping (GROUP BY) or UNION query that runs on this node could not read an input row, combine it into its group, or write a group's partial row, for an internal reason. The detail line names the first row and the reason; the grouping adapter's REST counts the rows not read and the writes that failed, by reason. | Report it to MetaFluent support with the log around the message; the detail lines under the same code and the query text, if known, are needed. |
| `MF-SYN-010` Some rows of a &lt;statementKind&gt; query could not be written to its result on this node; later failures of the query are counted, not logged. | `WARNING` | The adapter that holds the computed rows of a grouping (GROUP BY) or UNION query could not write a row or its image, for an internal reason, so that row may be missing or out of date in the result. The detail line names the first row and the reason; the adapter's REST counts the failures, by reason. | Report it to MetaFluent support with the log around the message; the detail lines under the same code and the query text, if known, are needed. |

### Refresh server

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-RFR-005` The refresh server could not set up some rows of a client's query, so those rows are not served, or are served as access denied. | `WARNING` | Rows of a query result could not be made or set up on the refresh server for one client connection: the row's table is not available on this server, its content is unknown, or its data could not be read. The first such row is reported; later ones on the same connection are counted on the refresh server's shard statistics. | Report it to MetaFluent support with the log around the message; the detail line that follows it names the shard, the first row and its failure. |

### Query handling

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| `MF-QRY-117` A client's query was refused because the query server could not read its analysis. | `WARNING` | The query was analysed, but the query server serving the client's connection could not read the result of that analysis, so the client was told the query is refused. A repeat of the query is analysed again. | Report it to MetaFluent support with the log around the message; support needs the detail lines that follow it. |

---

## Where to go next

- [Operations: Logging](Operations-Logging.md) - how to query these messages live.
- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom-to-remedy, which references this catalog.
