# Deployment Cookbook: Fine-Grained

The same capabilities as [Static MDS](Cookbook-Deploy-Static-MDS.md), with each service running separately instead of consolidated together. Every service - session, pub/sub, SQL, orchestration, the gateway, admin, and each projector - runs on its own, so you can place it, size it, and make it redundant on its own terms.

**Audience:** Architect, Operator. Choose this when you want isolation between services, or want to make individual services redundant.

This is the **Scalable, fine-grained, multi-homed** topology in [Architecture: Advanced](Architecture-Advanced.md#scalable-fine-grained-multi-homed) run at fixed capacity - read that for the full picture; install here first and learn the details later.

---

## The same images, three ways to run them

Every method below runs the **identical images** (`ghcr.io/metafluent-dist-nn/mf-*`) with the **identical `deployment-config/`** - only the way you launch them differs:

| Method | You launch it with | Ideal for |
|--------|--------------------|-----------|
| **Conventional** | the host `./run` launcher | the standard install - this is the primary path |
| **Docker** | `docker compose up` | a demo or lab on a single machine |
| **Kubernetes** | standard `Deployment` / `Service` manifests | a cluster-managed fixed install |

The consolidated `mf-core-srvcs` of the Static MDS deployment simply becomes its four constituent services here. The projector images are unchanged.

---

## Images you need

| Image | Role | Release |
|-------|------|---------|
| `mf-api-gateway` | REST entry point for the cluster | [`deploy-mf-api-gateway`](https://github.com/MetaFluent-Dist-NN/deploy-mf-api-gateway/releases/tag/MILESTONE-v6.0.0) |
| `mf-admin` | ResourceStore (config), network registry, central log | [`deploy-mf-admin`](https://github.com/MetaFluent-Dist-NN/deploy-mf-admin/releases/tag/MILESTONE-v6.0.0) |
| `mf-session` | Authenticates clients and issues session identity | [`deploy-mf-session`](https://github.com/MetaFluent-Dist-NN/deploy-mf-session/releases/tag/MILESTONE-v6.0.0) |
| `mf-pubsub` | Serves publish/subscribe (topic) subscriptions | [`deploy-mf-pubsub`](https://github.com/MetaFluent-Dist-NN/deploy-mf-pubsub/releases/tag/MILESTONE-v6.0.0) |
| `mf-sql` | Serves SQL (relational) queries | [`deploy-mf-sql`](https://github.com/MetaFluent-Dist-NN/deploy-mf-sql/releases/tag/MILESTONE-v6.0.0) |
| `mf-orchestration` | Places and coordinates the projector tier | [`deploy-mf-orchestration`](https://github.com/MetaFluent-Dist-NN/deploy-mf-orchestration/releases/tag/MILESTONE-v6.0.0) |
| `mf-projector-mds` | MDS projector (ETA + MAMA adapters); run one or more | [`deploy-mf-projector-mds`](https://github.com/MetaFluent-Dist-NN/deploy-mf-projector-mds/releases/tag/MILESTONE-v6.0.0) |

See the [Image Catalog](Image-Catalog.md) for what each image contains. To try the platform without a live feed, add a simulator - see [Use a simulator](#use-a-simulator) below.

---

## Conventional Fine-Grained

The primary path: extracted images, run natively. Full mechanics are in [Deployment: Without Docker](Deployment-Without-Docker.md).

1. From each release above, download the installation-package zip and unpack it.
2. Edit each `deployment-config/` for your environment (see [Configuration: Basics](Configuration-Basics.md)). The packages ship working defaults; you change only what your environment needs.
3. Set `JAVA_HOME` and start each with `./run`.

Each service looks for the gateway at `mf-api-gateway:9090` by default. Point it at your gateway host whatever way suits your environment: set `METAFLUENT_API_GATEWAY_HOST` (and `METAFLUENT_API_GATEWAY_PORT`) in the launch environment, set the same values in `deployment-config/`, or map the name in your own name resolution. The launcher prints the value in effect at startup.

**Point the projector at its ETA server.** The ETA/MDS projector reads its feed from an ETA server given by `manager.etaServerHost` (port `etaServerPort`, default `14002`). It defaults to `localhost`, so if the feed runs on the same host as the projector there is nothing to set. For a feed on another host, set `METAFLUENT_ETA_SERVER_HOST` (or the property in `deployment-config/`) to its address.

### Isolation and redundancy, service by service

Because each service runs on its own, you can:

- **Place it where it belongs** - put a service on its own host or network, so different services can sit on different role networks (control, private, client).
- **Make it redundant on its own** - run two of any service that carries client state (session, pub/sub, SQL, orchestration) as an active/standby pair; one serves, the other stays hot and takes over in seconds. The mechanism is [Architecture: Advanced](Architecture-Advanced.md#high-availability-activestandby).
- **Add projector capacity and resilience** - want more throughput, or a feed that keeps flowing if one projector restarts? Run another `mf-projector-mds`. Projectors can each carry a different set of feeds (`METAFLUENT_ETA_FEED_INCLUSIONS` / `METAFLUENT_ETA_FEED_EXCLUSIONS`), exactly as in [Static MDS](Cookbook-Deploy-Static-MDS.md#serving-different-feeds-from-different-projectors).

---

## Docker Fine-Grained

Docker Compose brings every service up on a single machine, ideal for a demo or a lab. For production, use the conventional or Kubernetes install.

Save this as `docker-compose.yml` and run `METAFLUENT_HOST_UID=$(id -u) docker compose up -d`:

```yaml
services:

  mf-api-gateway:
    image: ghcr.io/metafluent-dist-nn/mf-api-gateway-cfg-stable:milestone
    container_name: mf-api-gateway
    network_mode: host
    environment: { METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}" }
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-admin:
    image: ghcr.io/metafluent-dist-nn/mf-admin-cfg-stable:milestone
    container_name: mf-admin
    network_mode: host
    environment: { METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}" }
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-session:
    image: ghcr.io/metafluent-dist-nn/mf-session-cfg-stable:milestone
    container_name: mf-session
    network_mode: host
    environment: { METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}" }
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-pubsub:
    image: ghcr.io/metafluent-dist-nn/mf-pubsub-cfg-stable:milestone
    container_name: mf-pubsub
    network_mode: host
    environment: { METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}" }
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-sql:
    image: ghcr.io/metafluent-dist-nn/mf-sql-cfg-stable:milestone
    container_name: mf-sql
    network_mode: host
    environment: { METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}" }
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-orchestration:
    image: ghcr.io/metafluent-dist-nn/mf-orchestration-cfg-stable:milestone
    container_name: mf-orchestration
    network_mode: host
    environment: { METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}" }
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-projector-mds:
    image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
    container_name: mf-projector-mds
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_MAMA_DISABLED: "true"   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]
```

`METAFLUENT_HOST_UID` gives the in-container user your host UID, so the bind-mounted `./logs` and `./data` stay writable. Run more projectors, partitioned by feed, the same way as in Static MDS.

---

## Kubernetes Fine-Grained

An example. It runs the same images and `deployment-config/` as the other two methods: one `Deployment` per service, and a `Service` for each name other services address.

```yaml
# Each service: a Deployment plus a Service on the name others address it by.
# Shown for the gateway; session, pubsub, sql, orchestration, and admin follow
# the identical pattern with their own image and port.
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-api-gateway }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-api-gateway } }
  template:
    metadata: { labels: { app: mf-api-gateway } }
    spec:
      containers:
        - name: mf-api-gateway
          image: ghcr.io/metafluent-dist-nn/mf-api-gateway-cfg-stable:milestone
---
apiVersion: v1
kind: Service
metadata: { name: mf-api-gateway }
spec:
  selector: { app: mf-api-gateway }
  ports: [ { port: 9090, targetPort: 9090 } ]
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-session }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-session } }
  template:
    metadata: { labels: { app: mf-session } }
    spec:
      containers:
        - name: mf-session
          image: ghcr.io/metafluent-dist-nn/mf-session-cfg-stable:milestone
---
apiVersion: v1
kind: Service
metadata: { name: mf-session }
spec:
  selector: { app: mf-session }
  ports: [ { port: 8900, targetPort: 8900 } ]
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-projector-mds }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-projector-mds } }
  template:
    metadata: { labels: { app: mf-projector-mds } }
    spec:
      containers:
        - name: mf-projector-mds
          image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
          env:
            - { name: METAFLUENT_MAMA_DISABLED, value: "true" }   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
```

To make a service redundant, raise its `replicas` (or add a second `Deployment`); the active/standby election picks which instance serves. To add projector capacity or a feed partition, add another projector `Deployment`.

---

## Use a simulator

To evaluate the platform without a live feed, add the `mf-eta-simulator` image - a synthetic ETA source that replays recorded content, so your projectors have something to serve.

| Image | Role | Release |
|-------|------|---------|
| `mf-eta-simulator` | Synthetic ETA data source | [`deploy-mf-eta-simulator`](https://github.com/MetaFluent-Dist-NN/deploy-mf-eta-simulator/releases/tag/MILESTONE-v6.0.0) |

Run it the same way as everything else: as another `./run` package, another Compose service, or another `Deployment`. The Compose stanza is the same as in [Static MDS](Cookbook-Deploy-Static-MDS.md#use-a-simulator) - and the projector already finds it at the `localhost` default, nothing to set.

---

## Going further

- [Static MDS](Cookbook-Deploy-Static-MDS.md) - the consolidated starting point this page decomposes.
- [Static MDS with Compute](Cookbook-Deploy-Static-Compute.md) - add a compute tier that derives computed content.
- [Scalable MDS](Cookbook-Deploy-Scalable.md) - let the projector tier grow and shrink with load automatically.
- Serving real, entitled Refinitiv data? See [Configure DACS](Cookbook-Configure-DACS.md) to turn on authentication and entitlement checks.

---

## Where to go next

- [Confirm it's running](Operations-Monitoring.md#is-the-system-healthy) - check every component's health once the deployment is up.
- [Architecture: Advanced](Architecture-Advanced.md#scalable-fine-grained-multi-homed) - the topology this page deploys, and why.
- [Deployment: Without Docker](Deployment-Without-Docker.md) - the conventional install mechanics in full.
- [Image Catalog](Image-Catalog.md) - what each image contains.
- [Configuration: Basics](Configuration-Basics.md) - what the configuration you supply contains.
