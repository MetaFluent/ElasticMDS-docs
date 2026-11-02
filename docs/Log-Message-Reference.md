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

> Sections are added as they are catalogued. Template for a new component:

### &lt;Component name&gt; (`<logger name>`)

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| _(to be catalogued)_ | | | |

---

## Where to go next

- [Operations: Logging](Operations-Logging.md) - how to query these messages live.
- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom-to-remedy, which references this catalog.
