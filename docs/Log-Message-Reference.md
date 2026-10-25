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

> Sections are added as they are catalogued. Template for a new component:

### &lt;Component name&gt; (`<logger name>`)

| Message | Level | Meaning | Action |
|---------|-------|---------|--------|
| _(to be catalogued)_ | | | |

---

## Where to go next

- [Operations: Logging](Operations-Logging.md) - how to query these messages live.
- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom-to-remedy, which references this catalog.
