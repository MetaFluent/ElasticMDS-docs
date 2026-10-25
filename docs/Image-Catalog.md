# Deployment: Image Catalog

This page lists the deployable Elastic MDS images, grouped by the role they play in a deployment.
Use it to answer "which image do I run for X."

**Audience:** Architect, Operator.

Every image is published to your private GitHub Container Registry, `ghcr.io/metafluent-dist-nn` (`NN` is the
number of your MetaFluent distribution organization - see [Deployment: Basics](Deployment-Basics.md#your-metafluent-github-organization)), and each is
operated through a corresponding `deploy-mf-*` deployment project - the unit you clone, configure,
and run. The **Deploy project** column names each project, and links to its repository in your organization where you can clone it. How to authenticate to
the registry, configure an image, and (optionally) bake a configured image are covered in
[Deployment: Basics](Deployment-Basics.md); how images are arranged into a running cluster is covered
in [Architecture: Advanced](Architecture-Advanced.md) and the Deployment pages. Images are referenced
by the `stable` tag.

---

## Client-facing query services

The services a client application connects to. A deployment runs these separately, or
uses the consolidated image that packages them together.

| Image | What it is / includes | Deploy project |
|-------|-----------------------|----------------|
| `mf-session` | Terminates and authenticates client connections and issues the session identity the other services trust. | [`deploy-mf-session`](https://github.com/MetaFluent-Dist-NN/deploy-mf-session) |
| `mf-sql` | Serves SQL (relational) queries over the client protocol. | [`deploy-mf-sql`](https://github.com/MetaFluent-Dist-NN/deploy-mf-sql) |
| `mf-pubsub` | Serves publish/subscribe (topic) subscriptions over the client protocol. | [`deploy-mf-pubsub`](https://github.com/MetaFluent-Dist-NN/deploy-mf-pubsub) |
| `mf-core-srvcs` | The session, SQL, and pub/sub services plus the orchestration coordinator, packaged in a single image - the consolidated alternative to running them separately. | [`deploy-mf-core-srvcs`](https://github.com/MetaFluent-Dist-NN/deploy-mf-core-srvcs) |

---

## Projectors

Projectors bring content into the platform. Each projector image hosts the content adapter(s) for
one kind of source; a deployment runs the projectors it needs.

### Market data feeds

| Image | What it is / includes | Deploy project |
|-------|-----------------------|----------------|
| `mf-projector-eta` | Sources a Refinitiv ETA (Elektron Transport API) feed. | `deploy-mf-projector-eta` |
| `mf-projector-mama` | Sources OpenMAMA-bridged feeds (for example RDF-RMDS). The native bridge libraries are licensed and supplied by the operator, not baked into the image. | `deploy-mf-projector-mama` |
| `mf-projector-mds` | The ETA and MAMA adapters combined in a single image. | [`deploy-mf-projector-mds`](https://github.com/MetaFluent-Dist-NN/deploy-mf-projector-mds) |

### Reference data

| Image | What it is / includes | Deploy project |
|-------|-----------------------|----------------|
| `mf-projector-rdbms` | Exposes tables from any JDBC-compliant relational database as content. The JDBC driver is supplied by the operator. | `deploy-mf-projector-rdbms` |
| `mf-projector-socrata` _(forthcoming)_ | Exposes datasets from a Socrata open-data platform as content. | _(forthcoming)_ |

### Computed content

| Image | What it is / includes | Deploy project |
|-------|-----------------------|----------------|
| `mf-projector-compute` | Derives computed and interpolated content from other projectors' output, rather than sourcing an external feed. Customizable with different computation libraries. | `deploy-mf-projector-compute` |

The compute projector hosts **computation libraries**. The `intrinsic` library is built into the
base platform and always present; the others are available.

- **`intrinsic`** - the built-in SQL arithmetic and comparison operators: `+`, `-`, `*`, `/`, `=`, `<`, `<=`, `>`, `>=`. Always available as part of the base platform.
- **`basic`** - elementary utility functions: ripple, timer, and update-tracking fields.
- **`math`** - mathematical and statistical functions: minimum, maximum, average, weighted moving average, and random.
- **`interpolation`** - curve interpolation (polynomial, and by index or date), plus ad-hoc expression fields.
- **`dates`** _(forthcoming)_ - date manipulation functions.
- **`finance`** _(forthcoming)_ - finance-related mathematical functions.

---

## Control plane and orchestration

The services that manage a deployment's scale and lifecycle. Orchestration decides; a container
manager carries the decisions out on the underlying platform.

| Image | What it is / includes | Deploy project |
|-------|-----------------------|----------------|
| `mf-orchestration` | Makes the placement, rebalancing, and scale decisions for the projector tier. | [`deploy-mf-orchestration`](https://github.com/MetaFluent-Dist-NN/deploy-mf-orchestration) |
| `mf-dcm` | Carries out orchestration's decisions on Docker / Docker Compose (starts and stops projector containers). | `deploy-mf-dcm` |
| `mf-k8s-cm` | Carries out orchestration's decisions on Kubernetes (starts and stops projector pods). The production choice. | `deploy-mf-k8s-cm` |

---

## Platform infrastructure

Cluster-wide services a deployment needs regardless of its content.

| Image | What it is / includes | Deploy project |
|-------|-----------------------|----------------|
| `mf-api-gateway` | The cluster's REST entry point; routes each request to the node that owns the endpoint. | [`deploy-mf-api-gateway`](https://github.com/MetaFluent-Dist-NN/deploy-mf-api-gateway) |
| `mf-admin` | Configuration storage (ResourceStore), the network registry, and the centralized log service. | [`deploy-mf-admin`](https://github.com/MetaFluent-Dist-NN/deploy-mf-admin) |

---

## All-in-one and evaluation

Single-image deployments for evaluation, labs, and small footprints.

| Image | What it is / includes | Deploy project |
|-------|-----------------------|----------------|
| `mf-mds-consolidated` | A complete market-data server in one image - session, SQL, pub/sub, push and refresh distribution, orchestration, entitlements, configuration storage, and the ETA/MAMA content adapters. The image the [Quick Start](Quick-Start.md) runs, and the place to start evaluating Elastic MDS. | [`deploy-mf-mds-consolidated`](https://github.com/MetaFluent-Dist-NN/deploy-mf-mds-consolidated) |
| `mf-eta-simulator` | A synthetic data source that replays recorded content over the ETA protocol, so a deployment has something to serve without a live feed. | [`deploy-mf-eta-simulator`](https://github.com/MetaFluent-Dist-NN/deploy-mf-eta-simulator) |

---

## Where to go next

- [Deployment: Basics](Deployment-Basics.md) - authenticating to the registry, configuring an image, and baking a configured image.
- [Architecture: Advanced](Architecture-Advanced.md) - how these images are arranged into deployment topologies.
- [Glossary](Glossary.md) - definitions of the terms used here.
