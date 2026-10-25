# Dynamic Data Conventions

Content is delivered as JMS `MapMessage`s. This page explains how to interpret them: the message types, the state of a data stream, and the header properties that carry both. It is the companion reference to [JMS Application Development](Develop-JMS.md).

**Audience:** developers processing content in a JMS (or JDBC) application.

The `com.metafluent.jms.common.DynamicDataConventions` class defines every property name and type code described here; applications use those constants rather than literal strings or numbers.

---

## Map messages and data streams

Content arrives as JMS `MapMessage`s. Each message carries standard and MetaFluent-specific **properties** (in the JMS header) and a **map of named fields** (the data). Fields have primitive types - `double`, `long`, `String`, `boolean`, and so on - and an application reads them by iterating the map or accessing fields by name.

A **data stream** is the sequence of messages for one unit of content delivered to one subscriber. Each stream has an independent lifecycle and state. An application that subscribes to several topics receives several streams, each with its own state.

---

## Message types

Every message carries its type in the `JMS_METAFLUENT_MSG_TYPE` property. An application reads it and dispatches (as `SimpleSubscriber` does):

| Type | Meaning |
|------|---------|
| **IMAGE** | The complete set of initial field values for a stream, sent when the subscription is established. May also carry a data-condition indication. |
| **UPDATE** | A change to one or more field values. Does not change stream state. |
| **STATUS** | A change in the data condition or stream state (see below). Carries no field data. |
| **STREAM_UPDATE** | On a multi-stream topic, signals a new stream or a change in ordering. Carries no field data; apply these in the order received. |
| **CORRECTION** | *(Defined but not currently emitted.)* A change to field values not arising from market activity. |
| **RESET** | *(Defined but not currently emitted.)* A change from administrative activity, such as the daily close. |

---

## Stream state

A stream's state is carried in the `JMS_METAFLUENT_STATE` property. It is optional; if absent, assume `OK`.

| State | Meaning |
|-------|---------|
| **OK** | The data for this stream is current. |
| **STALE** | The data is suspect (for example, the source has disconnected). The provider will try to recover the stream with a fresh image - **do not re-subscribe**. |
| **DENIED** | The requester is not entitled to the content. It can arrive on the initial request or later (entitlements changed). For a single-stream topic, close the subscription. |
| **INVALID** | The request is erroneous and can never be satisfied. Do not resubmit it. |
| **CLOSED** | The stream has been closed. It may become available later, so re-opening it at some later time is reasonable. |

Rules that always hold:

- On a stream that delivers an image, the image always arrives before any update.
- Updates may arrive on a stale stream.
- `JMS_METAFLUENT_TEXT` carries human-readable information about a status. Display it, but do not parse it as the basis for a decision - act on the state code.

---

## Header properties

| Property | Type | Purpose |
|----------|------|---------|
| `JMS_METAFLUENT_MSG_TYPE` | byte | The message type (above). Present on every content message. |
| `JMS_METAFLUENT_STATE` | byte | The stream state (above). Optional; absent means `OK`. |
| `JMS_METAFLUENT_TEXT` | String | Informational text about a status. May be empty but is never null. |
| `JMS_METAFLUENT_ID` | long | Identifies a stream within a multi-stream topic. Single-stream topics omit it. Treat the value as opaque. |
| `JMS_METAFLUENT_NEXT_ID` | long | In an ordered collection, the next stream's id (`-1` if last). Present only in `STREAM_UPDATE`. |
| `JMS_METAFLUENT_PREV_ID` | long | In an ordered collection, the previous stream's id (`-1` if first). Present only in `STREAM_UPDATE`. |
| `JMS_METAFLUENT_SYNC` | boolean | Appears once per multi-stream subscription, on a collection-level status message, to signal the collection is complete. |

---

## Multi-stream topics

A **multi-stream topic** delivers several data streams over a single subscription - a collection such as a portfolio, a yield curve, an order book, or the result of a query. Conceptually the streams are the rows of a table. The subscription itself is ordinary; what differs is that the application also receives `STREAM_UPDATE` messages describing the collection's structure.

**Stream identifiers.** Each stream in a collection has a unique integer id, in `JMS_METAFLUENT_ID`. A `STREAM_UPDATE` also carries the ids of the next and previous streams (`JMS_METAFLUENT_NEXT_ID` / `JMS_METAFLUENT_PREV_ID`); a next of `-1` marks the tail of the collection and a previous of `-1` marks the head. Ids are unique for the life of the collection and are not reused; do not assume they are sequential. A `STREAM_UPDATE` may also carry human-readable text in `JMS_METAFLUENT_TEXT` for display or logging - do not use it to identify a stream, as it may not be unique.

**Initialization.** On subscribing, the application receives a sequence of `STREAM_UPDATE` messages until its view of the collection matches the provider's; these may not arrive in collection order. When the initial collection is complete, the provider sends one collection-level status message carrying `JMS_METAFLUENT_SYNC = true` (a status with no stream id) - useful for sizing a display or allocating resources.

**Ordering.** An application that maintains the collection's order must process `STREAM_UPDATE` messages strictly in the order received; otherwise its view diverges from the provider's. The provider sends the minimum messages needed - a re-ordering that moves one stream is often a single update. A collection may be static (no changes once complete) or dynamic (streams added, removed, or re-ordered later); design for the dynamic case.

- **Adding a stream** - a `STREAM_UPDATE` with a new id and its next/previous ids.
- **Removing a stream** - a `STATUS` message with state `CLOSED` for that stream; reconnect its neighbours and reassign head/tail as needed.

**Per-stream state.** Each stream in a collection follows the same state model as a single-stream topic, and a `STREAM_UPDATE` is always the first message for a stream. A stream marked `DENIED` is still part of the underlying collection but is not visible to this application - continue to maintain it. A status message with **no** stream id applies to the collection as a whole (for example, when the subscriber is not entitled to the collection itself).

An application that does not need the collection's structure can ignore the `STREAM_UPDATE` messages and process only the stream data.

---

## Where to go next

- [JMS Application Development](Develop-JMS.md) - subscribing, contexts, and selectors.
- [Glossary](Glossary.md) - definitions of the terms used here.
