# What's New in Elastic MDS

This page is for existing MetaFluent v5 customers. It sets out what Elastic MDS adds beyond the v5
platform you already run.

**Audience:** existing MetaFluent v5 customers.

**v5 application code is fully compatible and runs unchanged.** The v5 compatibility details are in
[JMS Application Development](Develop-JMS.md#compatibility-with-v5).

---

## Automatic slow-consumer management

A distribution server fans the same updates out to many independent consumer connections. When one
consumer - its application, its network, or a downstream system - cannot keep pace, its unread data
backs up on the server and, left unmanaged, degrades delivery for the other consumers sharing that
server. Elastic MDS manages this **automatically**, within the standard distribution
infrastructure:

- **No code changes.** Slow-consumer handling is a property of the platform. Applications adopt it
  by doing nothing.
- **Transparent to applications.** A consumer that falls behind is kept current without being
  disconnected and without an error it has to handle.
- **One infrastructure.** There is no separate slow-consumer tier or add-on product to deploy and
  operate. The same distribution servers that deliver your content also protect it.

The protection is **multi-level**. The platform continuously profiles each consumer connection and
responds in order of least disruption first:

- **Split before conflate.** Where it can, the platform first **splits** a consumer's stream across
  additional connections, spreading the load so the consumer is served within capacity. This
  mitigation is transparent and carries **no data loss**.
- **Conflate only when it must.** A connection that still cannot sustain the offered rate has
  **conflation** engaged for that connection alone: updates arriving in a short window are coalesced
  into a single update carrying the current value. The slow consumer receives fewer messages but
  always the latest data - never stale, never silently dropped - and consumers keeping up are left
  untouched. Conflation is **disengaged automatically** when the connection recovers.

The mechanism, including how each connection's capacity ceiling is learned rather than fixed, is
described in [Architecture: Advanced](Architecture-Advanced.md#slow-consumer-protection-delivery-scaling-and-conflation).

---

## JMS selectors

Elastic MDS implements the JMS message **selector** for content subscriptions. A subscription can
carry a selector that controls what the application receives, so an application sees **only the
fields it wants** - which reduces the bandwidth consumed, since both image and update messages carry
fewer fields, and the CPU used on the client.

- **A very minor application change.** Adopting a selector is a single string passed when the
  subscriber is created; the rest of the application is unchanged.
- **Selectors work under the v5 context.** A v5 application on `com.metafluent.jms_context.mds` can
  adopt them without moving to the new MarketData context.

A selector does more than choose fields - it can rename a field with `AS`, compute a derived field
from an expression, and constrain the update stream with a `WHERE` clause so an update is delivered
only when a condition holds. The full grammar and examples are in
[JMS Application Development](Develop-JMS.md#selectors).

---

## System-wide monitoring and control

Elastic MDS gives an operator a **centralized, fine-grained line of sight to the entire
deployment**, regardless of how many containers it spreads across. Each component reports its
health, role, and live statistics through one API, which drives both a dashboard and direct
programmatic access:

- **REST API.** Each operational query - component health, active/standby roles, connection and
  consumer statistics, whether conflation is currently engaged on a connection - is available over a
  standard REST interface, addressed through the API gateway. It is the control and observation
  interface for the whole cluster, and the dashboard is built on it. See
  [Monitoring & Diagnostics](Operations-Monitoring.md) and the [REST API](REST-API.md) reference.
- **Dashboard.** A graphical [Dashboard](Dashboard.md) presents the same system-wide state visually, for
  operators who prefer that to issuing queries directly.

---

## Where to go next

- [Architecture: Basics](Architecture-Basics.md) - the model these capabilities build on, then
  [Architecture: Advanced](Architecture-Advanced.md) for the deployment, resilience, and
  slow-consumer detail.
- [JMS Application Development](Develop-JMS.md) - selectors, contexts, and how v5 code carries over.
- [Monitoring & Diagnostics](Operations-Monitoring.md) - seeing a running deployment through the
  gateway.
- [Quick Start](Quick-Start.md) - stand up a deployment and watch data flow.
