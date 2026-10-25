# AI-Assisted Troubleshooting

> **Preview - under active development.** This capability is not yet generally available. It is described here to show where operations with Elastic MDS is heading; the examples below are illustrative.

Everything on the [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md), [Operations: Monitoring & Diagnostics](Operations-Monitoring.md), and [Operations: Logging](Operations-Logging.md) pages, an experienced engineer can do by hand over REST. AI-assisted troubleshooting puts that expertise behind a conversation: you describe the symptom, and an assistant runs the probes, gathers the evidence, and explains what it found - in plain language.

**Audience:** Operator, Developer.

---

## What it does

An AI support assistant drives the same REST and log surface you do, and knows how to use it the way an expert would:

- **Pull and analyze diagnostic dumps.** It retrieves DataFabric dumps over the REST API - the deep internal state of the system - and analyzes them for anomalies and errors, the kind of reading that today takes an engineer.
- **Read and correlate logs.** It queries the centralized log service across every component, follows a cascade back to the first cause, and summarizes what happened.
- **Run targeted live probes.** It issues the same application-state, push, and orchestration queries documented on the [REST API](REST-API.md) page to confirm a hypothesis against the running system.

---

## What it might look like

> Illustrative - these show the intended experience; exact phrasing and coverage are evolving.

- *"Why did mf-mds-consolidated go to RECOVERING around 10:30?"* - the assistant reads the state history and the logs, points at the ETA feed drop, and shows the reconnect.
- *"Is any consumer being conflated, and why?"* - it queries the shards, finds the slow consumer, and explains what triggered the protection.
- *"Pull a fabric dump for the projector and tell me if anything looks off."* - it captures the dump and reports what it found.

---

## Where it fits

The assistant **complements** the manual tools - it does not replace them. Everything it does, you can still do yourself with the pages above, and you always see the evidence it worked from. It is aimed especially at the [capture-and-analyze step](Operations-Troubleshooting.md#standard-diagnostic-procedure): gathering the state, dump, and logs the moment a problem appears, and making sense of them fast.

---

## Where to go next

- [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - the manual symptom-to-remedy guide.
- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - the health checks it builds on.
- [REST API](REST-API.md) - the query surface it drives.
