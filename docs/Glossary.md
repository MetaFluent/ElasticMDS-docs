# Glossary

Definitions of the terms used across this documentation. Each term is defined once here; other pages link back to it.

**Audience:** all readers.

---

**API gateway** - The deployment's REST control surface. It aggregates every component in a deployment so that a single request can read state or statistics from across the system. It is addressed by the convention name `mf-api-gateway`. See [Operations: Monitoring & Diagnostics](Operations-Monitoring.md).

**Composition** - A Docker Compose recipe that wires a set of Elastic MDS images together into a running deployment - for example, the Docker Compose file behind the [Demo](Cookbook-Deploy-Demo.md) cookbook entry, the one the [Quick Start](Quick-Start.md) uses. Compositions are **worked templates** for the deployment topologies: ideal for development, evaluation, and single-host lab or on-premises use, and a starting point you adapt. A conventional install needs no composition at all, and production at scale runs the same service catalog on **Kubernetes**. See [Deployment: Basics](Deployment-Basics.md) and [Deployment: Advanced](Deployment-Advanced.md).

**Content** - The data Elastic MDS delivers to applications, whether real-time (continuously updating) or static. Content is represented as tables of fields; each unit of content is identified so that an application can request it and the platform can locate and deliver it.

**Content adapter** - A component that understands a particular kind of data source - a market-data feed, a relational database, a set of files - and represents that source's data as Elastic MDS content. Each source type has its own adapter; the rest of the system works against content uniformly.

**Content table** - The representation of content as a set of fields with identified rows. Applications read content tables with SQL or subscribe to them by topic.

**Context** - The named context an application selects (the `-context` value, or the `ContextName` property), which determines the topic-naming convention. Applications written for MetaFluent v5 use `com.metafluent.jms_context.mds` and get the v5 `feed.symbol` grammar, unchanged; `MarketData-6.0.0` is an explicit opt-in for generic, schema-qualified addressing. See [JMS Application Development](Develop-JMS.md).

**Deployment project** - A repository that packages the configuration and the `start` / `stop` scripts for running one Elastic MDS image - for example, `deploy-mf-mds-consolidated`. Each deployment project pairs with a corresponding image; the [Image Catalog](Image-Catalog.md) lists them. See [Deployment: Basics](Deployment-Basics.md).

**Distribution** - How requested content reaches an application over the wire. Elastic MDS delivers content by push or by refresh (see those entries). See [Architecture: Advanced](Architecture-Advanced.md).

**Elastic MDS** - MetaFluent's Market Data System: an enterprise platform that gives applications unified, standards-based access to real-time and non-real-time content. It is built on the StreamLens framework.

**Entitlement** - A rule that controls which content an application or user may access. Elastic MDS enforces the entitlements of the underlying data sources, at the row and field level where required. See [Access Control](Access-Control.md).

**Image** - In push distribution, the initial snapshot of a content item's current field values, delivered when an application first subscribes, ahead of any updates. See [JMS Application Development](Develop-JMS.md).

**Interest-driven** - The principle that content is ingested and kept current only while an application is interested in it; when no application is interested, the resources holding it can be released.

**Projector** - A deployable unit that hosts one or more content adapters. A deployment runs one or more projectors, each responsible for some set of content.

**Push** - A distribution mode in which each change to a content item is sent to the subscribing application as it happens. See [Architecture: Advanced](Architecture-Advanced.md).

**Query** - How an application states the content it wants, using SQL or a topic subscription. An application does not need to know which adapter or host holds the data.

**Refresh** - A distribution mode in which the application reads the current values of content when it needs them, rather than receiving every change. See [Architecture: Advanced](Architecture-Advanced.md).

**Session** - An application's authenticated connection to Elastic MDS, together with the context under which it accesses content.

**Simulator** - A component that replays recorded market data as a stream, used to supply content for evaluation without connecting a real data source - the `mf-eta-simulator` in the [Quick Start](Quick-Start.md).

**StreamLens** - The integration framework that Elastic MDS is built on. It provides the platform services - session management, content orchestration, distribution, and monitoring - that content services use.

**Topic** - The name by which an application subscribes to a unit of content over JMS. How a topic name is interpreted depends on the context in effect (see Context).

**Update** - In push distribution, a message carrying a change to a content item's field values, delivered after the initial image. See [JMS Application Development](Develop-JMS.md).
