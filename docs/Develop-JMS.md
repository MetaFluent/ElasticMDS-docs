# JMS Application Development

This guide shows how to build a JMS application that subscribes to content from Elastic MDS. Elastic MDS is a JMS provider: you use the standard JMS API - either the `javax.jms` or the `jakarta.jms` namespace is supported - and the MetaFluent provider supplies the connection factory, connection, session, and subscriptions.

**Audience:** Java developers (the same model applies to the .NET and C bindings). No prior MetaFluent knowledge assumed.

Applications written for MetaFluent v5 run unchanged - see [Compatibility with v5](#compatibility-with-v5).

---

## The SDK

The provider and the example applications ship in the **MetaFluent JMS SDK** (`jms-sdk`). The current milestone is on the `stable` branch:

```
git clone --depth 1 -b stable git@github.com:MetaFluent-Dist-NN/jms-sdk.git
```

To use a specific milestone, clone its tag instead - for example `-b MILESTONE-v6.2.0`. Milestone tags follow the `MILESTONE-v<major>.<minor>.<patch>` convention; releases are tagged `RELEASE-v<major>.<minor>.<patch>`.

The SDK contains:

- `lib/metafluent.jms.jar` - the JMS provider. Add this one jar to your classpath to build against Elastic MDS. It includes both the `javax.jms` and `jakarta.jms` interfaces, so you do not need a separate JMS API jar and can develop against either namespace.
- `examples/src/...` - the source for the example applications, including `SimpleSubscriber`. A `jakarta.jms` version of `SimpleSubscriber` is also provided.
- `bin/*.jar` - the examples prebuilt, so you can run them without building.

---

## A first subscription

`SimpleSubscriber` (in the SDK) is a complete, console-based subscriber. Its structure is the standard JMS pattern:

1. Create a `TopicConnectionFactory` from the MetaFluent provider, given the address of the session server.
2. Set the **context** the session will use (see [Addressing content](#addressing-content-contexts-and-topic-names)).
3. Create a `TopicConnection` and a `TopicSession`.
4. For each topic, create a `Topic` and a `TopicSubscriber`, and register a `MessageListener`.
5. Start the connection.

Run the prebuilt subscriber against a running deployment, subscribing to one instrument:

```
java -cp "bin/SimpleSubscriberApplication.jar:lib/*" \
     com.metafluent.examples.simplesub.SimpleSubscriber \
     -connect mf-session:8900 -context com.metafluent.jms_context.mds RDF.VOD.L
```

`mf-session` is the conventional name for the session server your application connects to. Map it to your deployment's session host - the same way the [Quick Start](Quick-Start.md) maps `mf-api-gateway` - or use the `host:port` your operator gives you. (On the single-host Quick Start the session server runs on your own machine, so `localhost:8900` works there.)

The subscriber prints an `Image:` line (the initial field values) followed by `UPDATE:` lines as the values change. For a section-by-section walkthrough of the code, see [Worked Example: SimpleSubscriber](Example-SimpleSubscriber.md).

---

## Addressing content: contexts and topic names

An application names the content it wants with a JMS **topic**. How a topic name is interpreted is decided by the **context** the application selects - the value passed as `-context` (or set as the `com.metafluent.jms.client.Properties.ContextName` system property). There are two contexts.

### The v5 context (default, compatible)

Pass `com.metafluent.jms_context.mds` (or leave the context unset - the provider's built-in default is `com.metafluent.jms_context.mds-2`). Topic names use the v5 `feed.symbol` form, and the `Quotes` schema is implied:

| Topic | Resolves to |
|-------|-------------|
| `RDF.VOD.L` | schema `Quotes`, feed `RDF`, key `VOD.L` |
| `chain.RDF.0#.FTSE` | schema `Chains`, feed `RDF`, chain `0#.FTSE` |

This is exactly the v5 grammar. Existing applications keep working with no change.

### The MarketData context (explicit, generic)

Pass `MarketData-6.0.0`. Topic names are schema-qualified - you name the schema explicitly - in exchange for a more general addressing model.

Two capabilities are worth calling out. First, you can subscribe to a whole **table or view** by name - for example a saved portfolio view - and receive every row it contains, rather than naming a single instrument. Second, a single subscription can name **several keys at once** (a multi-key, or multi-stream, subscription), so one topic delivers a set of instruments. Both appear in the examples below.

| Topic | Resolves to |
|-------|-------------|
| `Quotes.RDF.VOD.L` | schema `Quotes`, table `RDF`, key `VOD.L` (a single instrument) |
| `Quotes.MyPortfolioView` | every row of the `MyPortfolioView` view (table-level subscription) |
| `Quotes.RDF.?KEY_=VOD.L,BT.A,BARC.L` | one subscription over several keys (multi-stream) |
| `Chains.RDF.0#.FTSE` | schema `Chains`, table `RDF`, chain `0#.FTSE` |

> **Note.** The bare-feed shorthand (`RDF.VOD.L`, `chain.RDF.0#.FTSE`) is understood **only** under the v5 context. Under `MarketData-6.0.0` you must write the schema-qualified form (`Quotes.RDF.VOD.L`); the bare form would be read as `schema.table.key` and would not name the same content.

---

## Selectors

A subscription can carry a **selector** that controls what you receive. With a selector, an application receives only the fields it needs, which reduces the bandwidth used and the CPU consumed on both the server and the client. The selector is passed when the subscriber is created (the `-selector` option in `SimpleSubscriber`) - for example `-selector "BID, ASK"` to receive just the bid and ask.

A selector can do more than choose fields:

- **Rename a field** with `AS` - `-selector "BID,ASK,TRDPRC_1 AS LAST"`.
- **Compute a derived field** with an expression - `-selector "BID,ASK,ASK-BID AS SPREAD"`.
- **Constrain the update stream** with a `WHERE` clause, so an update is delivered only when the condition holds - `-selector "BID,ASK,TRDPRC_1 WHERE TRDVOL_1 > 10000"`.

Selectors work the same way under either context, so a v5 application on the `com.metafluent.jms_context.mds` context can use them without moving to the MarketData context.

---

## Message types

Content is delivered as JMS `MapMessage`s. Each message carries a type, which the application reads from a message property and dispatches on (as `SimpleSubscriber` does):

- **Image** - the initial, complete set of field values for a topic, sent when the subscription is established.
- **Update** - a subsequent change to one or more field values.
- **Status** - a change in the state of the data stream: `OK`, `STALE` (the source may be disconnected), `CLOSED`, `DENIED` (not entitled), or `INVALID` (the request could not be satisfied).
- **Stream update** - on a multi-stream subscription (a table, view, or multi-key topic), signals a new stream or a change in the collection's ordering. An application that does not maintain collection order can ignore it.

Interpreting these messages correctly - the field and property conventions, the message-type and state codes, the multi-stream details, and how to read the field values - is covered in detail in [Dynamic Data Conventions](Dynamic-Data-Conventions.md). The `com.metafluent.jms.common.DynamicDataConventions` class defines the property names and type codes used throughout.

---

## Application design: threading and scalability

A subscriber receives messages on the provider's callback (message-listener) thread. Doing all of your processing on that thread is the simplest approach but limits throughput.

**Process off the callback thread.** For a scalable application, keep the callback thread's work to a minimum - typically just queuing each message for a separate worker thread or thread pool. This off-loads processing from the dispatch thread. If you use a pool, preserve the order of messages within a single stream. Moving work off the callback thread trades a little latency (the hand-off and its synchronisation) for throughput; careful design keeps that overhead small.

**Cache pattern.** An application that does not need to act on every message can have its worker threads apply updates into a cache, from which other threads read the current values. A GUI that refreshes a few times per second, rather than rendering every update, is the common case, and it markedly reduces load.

**Publishing and the session thread.** The JMS specification does not permit an application to asynchronously publish and subscribe on the same session. MetaFluent relaxes this: you may publish from a thread other than the JMS session thread even while subscribing asynchronously.

**GUI toolkits.** UI toolkits require that widgets be updated only on their own thread, so do not update the UI directly from the message callback. Marshal the update onto the UI thread - `SwingUtilities.invokeLater(...)` in Java Swing, or the delegate / `Control.Invoke(...)` mechanism in .NET Forms (a producer-consumer hand-off from the listener to the UI thread).

---

## Entitlements

An application can query the entitlements system on its own - checking whether an identity is permitted to access a unit of content, without subscribing to the content itself. This is done through a separate JMS context with its own topic conventions. See [Entitlements Context](Entitlements-Context.md).

---

## Compatibility with v5

Applications written for MetaFluent v5 run unchanged. Keep passing the `com.metafluent.jms_context.mds` context (or leave it unset) and the v5 `feed.symbol` topic grammar applies exactly as before. There is one parser, and the v5 grammar is a strict part of it - it does not drift.

What Elastic MDS (v6) adds is available on your terms:

- **Selectors** work with the v5 context, so you can adopt them without changing anything else.
- The **MarketData context** is an explicit opt-in for schema-qualified, generic addressing (arbitrary schemas, tables, views, and multi-key subscriptions).

---

## Where to go next

- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - interpreting the data in the messages you receive.
- [Architecture: Basics](Architecture-Basics.md) - the model behind the API.
- [Glossary](Glossary.md) - definitions of the terms used here.
- [JDBC Application Development](Develop-JDBC.md) - query the same content over JDBC.
- [Developing with TLS](Develop-TLS.md) - connect over TLS.
