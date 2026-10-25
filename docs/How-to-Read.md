# How to Read This Guide

**You do not read this guide front to back.** It is organized by topic so you can find things, but almost no one needs all of it. What you read depends on **what you are here to do** - and the routes below are deliberately short. Pick the one that matches your role, follow it in order, and treat everything else as reference you dip into when a specific need arises.

The sidebar is the full **topic map**. This page is the **role-specific routes** through it. If you are not sure which role fits, start with **New here** and branch out.

---

## New here / evaluating

You want to see what Elastic MDS is and watch it work, before committing to anything deeper.

1. [Home](index.md) - what Elastic MDS is, in two minutes.
2. [Quick Start](Quick-Start.md) - stand up a consolidated deployment with a simulator and watch data flow end to end.

That is the whole first look. Once it clicks, branch into the role below that matches what you will actually do.

---

## Application developer

**This is most readers.** You are writing an application that consumes content - prices, chains, whatever your business needs - and you do it through the standard APIs you already know: **JMS, JDBC, and SQL**. There is very little that is MetaFluent-specific to learn; the one concept that matters is the **MarketData context** - how a topic name maps to the content behind it.

1. [Quick Start](Quick-Start.md) - run the sample subscriber against a live deployment first, so you have something concrete.
2. [JMS Application Development](Develop-JMS.md) - the **MarketData context** and the topic model, on top of the plain `javax.jms` API. *(Prefer SQL? [JDBC Application Development](Develop-JDBC.md) gives you the same content through JDBC and a subset of SQL-92.)*
3. [Worked Example: SimpleSubscriber](Example-SimpleSubscriber.md) - a complete subscriber, walked through section by section.
4. [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - how images, updates, and status messages arrive, and how to read them.

*Optional:* [Entitlements Context](Entitlements-Context.md) - only if your application must enforce access control on behalf of its own users. Most applications never need it.

---

## Operator

You bring a deployment up and keep it healthy.

1. [Quick Start](Quick-Start.md) - the shortest path to a running system.
2. [Deployment: Basics](Deployment-Basics.md) - deployment projects, base images, and bringing a deployment up. *(Running natively instead of in Docker? [Deployment: Without Docker](Deployment-Without-Docker.md).)*
3. [Configuration: Basics](Configuration-Basics.md) - setting values and seeing what is actually in effect. *(Modes and environment substitution: [Configuration: Advanced](Configuration-Advanced.md).)*
4. [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - is it healthy, which part is not, and why.
5. [Operations: Logging](Operations-Logging.md) - querying the logs across the deployment.
6. [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md) - symptom to cause to remedy. **In an emergency, start here.**
7. [Security: Basics](Security-Basics.md) - REST/admin access, the cluster machine secret, and keeping the gateway on a trusted network; see [Access Control](Access-Control.md) for client authentication and entitlements.

The [REST API](REST-API.md) is the **control and management interface** behind the monitoring queries - reach for it when you want to script a check or build your own tooling.

---

## Architect

You decide the topology, how resilient it must be, how it is networked, and how it is secured.

1. [Architecture: Basics](Architecture-Basics.md) - the core model: services, adapters, projectors, the control plane, and the component-state lifecycle.
2. [Architecture: Advanced](Architecture-Advanced.md) - the deployment topologies, active/standby, auto-scaling, slow-consumer protection, and topology-based isolation.
3. [Deployment: Basics](Deployment-Basics.md) then [Deployment: Advanced](Deployment-Advanced.md) - the deployment model, and the networking that decides whether clients can reach it (bind vs advertise, flat vs segmented, substrate by substrate).
4. [Access Control](Access-Control.md) then [Security: Basics](Security-Basics.md) - client authentication and the entitlements (authorization) framework, then the operational security surfaces (REST/admin access, cluster secret, transport).

The [REST API](REST-API.md) is the control-plane to use if you are integrating monitoring or building tooling around a deployment.

---

## Already a MetaFluent v5 user

Your application code is **fully compatible and runs unchanged**. The new **MarketData** context unlocks new content and capabilities when you want them.

1. [JMS Application Development](Develop-JMS.md) - the MarketData context and the topic syntax it introduces.

From there, follow the **Application developer** path above - everything you already know still applies.

---

## Looking for something specific?

| You want to... | Go to |
|----------------|-------|
| Get content into an application | [JMS](Develop-JMS.md) / [JDBC](Develop-JDBC.md) |
| Stand up a running system | [Quick Start](Quick-Start.md) / [Deployment: Basics](Deployment-Basics.md) |
| Figure out why something is wrong | [Troubleshooting](Operations-Troubleshooting.md) |
| Understand how a piece works | [Architecture: Basics](Architecture-Basics.md) / [Architecture: Advanced](Architecture-Advanced.md) |
| Look up a term | [Glossary](Glossary.md) |

Every term used across the guide is defined in the [Glossary](Glossary.md).
