# Deployment Cookbook: Static MDS

The simplest real deployment: the core query services plus a set of MDS projectors that you size yourself. You choose how many projectors to run and start them, and when you want more throughput or more resilience you run another one.

**Audience:** Architect, Operator. The place to start a first production-style install.

This is the **Fixed-capacity, multi-homed** topology in [Architecture: Advanced](Architecture-Advanced.md#fixed-capacity-multi-homed) - read that for the full picture; install here first and learn the details later.

---

## The same images, three ways to run them

Every method below runs the **identical images** (`ghcr.io/metafluent-dist-nn/mf-*`) with the **identical `deployment-config/`** - only the way you launch them differs:

| Method | You launch it with | Ideal for |
|--------|--------------------|-----------|
| **Conventional** | the host `./run` launcher | the standard install - this is the primary path |
| **Docker** | `docker compose up` | a demo or lab on a single machine |
| **Kubernetes** | standard `Deployment` / `Service` manifests | a cluster-managed fixed install |

Pick the one that fits where you are running it. The configuration you write is the same in all three.

---

## Images you need

| Image | Role | Release |
|-------|------|---------|
| `mf-api-gateway` | REST entry point for the cluster | [`deploy-mf-api-gateway`](https://github.com/MetaFluent-Dist-NN/deploy-mf-api-gateway/releases/tag/MILESTONE-v6.0.0) |
| `mf-admin` | ResourceStore (config), network registry, central log | [`deploy-mf-admin`](https://github.com/MetaFluent-Dist-NN/deploy-mf-admin/releases/tag/MILESTONE-v6.0.0) |
| `mf-core-srvcs` | Session, SQL, pub/sub, and orchestration in one container | [`deploy-mf-core-srvcs`](https://github.com/MetaFluent-Dist-NN/deploy-mf-core-srvcs/releases/tag/MILESTONE-v6.0.0) |
| `mf-projector-mds` | MDS projector (ETA + MAMA adapters); run one or more | [`deploy-mf-projector-mds`](https://github.com/MetaFluent-Dist-NN/deploy-mf-projector-mds/releases/tag/MILESTONE-v6.0.0) |

See the [Image Catalog](Image-Catalog.md) for what each image contains. To try the platform without a live feed, add a simulator - see [Use a simulator](#use-a-simulator) below.

---

## Conventional Static MDS

The primary path: extracted images, run natively. Full mechanics are in [Deployment: Without Docker](Deployment-Without-Docker.md).

1. From each release above, download the installation-package zip and unpack it.
2. Edit each `app/config/deployment-config/` for your environment (see [Configuration: Basics](Configuration-Basics.md)). The packages ship working defaults; you change only what your environment needs.
3. For MAMA feeds, put your OpenMAMA libraries and bridge specification in place in the `mf-projector-mds` package - see [MAMA feeds](Deployment-Without-Docker.md#mama-feeds). For ETA feeds only, set `METAFLUENT_MAMA_DISABLED=true` for the projector.
4. Set `JAVA_HOME` and start each with `./run`. It starts the application in the background; use `./run --foreground` under a service manager.

Each service looks for the gateway at `mf-api-gateway:9090` by default. Point it at your gateway host whatever way suits your environment: set `METAFLUENT_API_GATEWAY_HOST` (and `METAFLUENT_API_GATEWAY_PORT`) in the launch environment, set the same values in `deployment-config/`, or map the name in your own name resolution. The launcher prints the value in effect at startup.

**Point the projector at its ETA server.** The ETA/MDS projector reads its feed from an ETA server given by `manager.etaServerHost` (port `etaServerPort`, default `14002`). It defaults to `localhost`, so if the feed runs on the same host as the projector there is nothing to set. For a feed on another host, set `METAFLUENT_ETA_SERVER_HOST` (or the property in `deployment-config/`) to its address.

### Adding capacity or resilience

Capacity is set by how many `mf-projector-mds` instances you run. Want more throughput, or want a feed to keep flowing if one projector restarts? Install and start another `mf-projector-mds`. You choose the number and bring them up.

### Serving different feeds from different projectors

Projectors in a pool can each carry a different set of feeds. Partition the feeds across them with one environment variable per instance:

| Instance | Environment | Carries |
|----------|-------------|---------|
| Projector A | `METAFLUENT_ETA_FEED_INCLUSIONS=BPIPE` | only the BPIPE feed |
| Projector B | `METAFLUENT_ETA_FEED_EXCLUSIONS=BPIPE` | every feed except BPIPE |

Set the variable in the launch environment, or in the projector's `deployment-config/`. That one variable is the only difference between the two instances - the image is the same.

---

## Docker Static MDS

Docker Compose brings the whole set up on a single machine, ideal for a demo or a lab. For production, use the conventional or Kubernetes install.

Save this as `docker-compose.yml` and run `METAFLUENT_HOST_UID=$(id -u) docker compose up -d`:

```yaml
services:

  mf-api-gateway:
    image: ghcr.io/metafluent-dist-nn/mf-api-gateway-cfg-stable:milestone
    container_name: mf-api-gateway
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  mf-admin:
    image: ghcr.io/metafluent-dist-nn/mf-admin-cfg-stable:milestone
    container_name: mf-admin
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  mf-core-srvcs:
    image: ghcr.io/metafluent-dist-nn/mf-core-srvcs-cfg-stable:milestone
    container_name: mf-core-srvcs
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  # Two projectors, partitioned by feed. Same image, one variable apart.
  mf-projector-mds-bpipe:
    image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
    container_name: mf-projector-mds-bpipe
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_MAMA_DISABLED: "true"   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
      METAFLUENT_ETA_FEED_INCLUSIONS: "BPIPE"       # carries only BPIPE
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  mf-projector-mds-other:
    image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
    container_name: mf-projector-mds-other
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_MAMA_DISABLED: "true"   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
      METAFLUENT_ETA_FEED_EXCLUSIONS: "BPIPE"       # carries every feed except BPIPE
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
```

`METAFLUENT_HOST_UID` gives the in-container user your host UID, so the bind-mounted `./logs` and `./data` stay writable. The two projector services show the feed partition from the previous section.

---

## Kubernetes Static MDS

An example. It runs the same images and `deployment-config/` as the other two methods, as ordinary Kubernetes objects: one `Deployment` per service, a `Service` for each name other services address, and two projector `Deployment`s carrying the feed partition.

```yaml
# --- gateway ---------------------------------------------------------------
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
metadata: { name: mf-api-gateway }      # cluster DNS name other services use
spec:
  selector: { app: mf-api-gateway }
  ports: [ { port: 9090, targetPort: 9090 } ]
---
# --- admin + core services -------------------------------------------------
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-admin }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-admin } }
  template:
    metadata: { labels: { app: mf-admin } }
    spec:
      containers:
        - name: mf-admin
          image: ghcr.io/metafluent-dist-nn/mf-admin-cfg-stable:milestone
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-core-srvcs }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-core-srvcs } }
  template:
    metadata: { labels: { app: mf-core-srvcs } }
    spec:
      containers:
        - name: mf-core-srvcs
          image: ghcr.io/metafluent-dist-nn/mf-core-srvcs-cfg-stable:milestone
---
# --- projectors: two instances, partitioned by feed ------------------------
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-projector-mds-bpipe }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-projector-mds-bpipe } }
  template:
    metadata: { labels: { app: mf-projector-mds-bpipe } }
    spec:
      containers:
        - name: mf-projector-mds
          image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
          env:
            - { name: METAFLUENT_MAMA_DISABLED, value: "true" }   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
            - { name: METAFLUENT_ETA_FEED_INCLUSIONS, value: "BPIPE" }
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-projector-mds-other }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-projector-mds-other } }
  template:
    metadata: { labels: { app: mf-projector-mds-other } }
    spec:
      containers:
        - name: mf-projector-mds
          image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
          env:
            - { name: METAFLUENT_MAMA_DISABLED, value: "true" }   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
            - { name: METAFLUENT_ETA_FEED_EXCLUSIONS, value: "BPIPE" }
```

To add capacity or resilience, add another projector `Deployment`, or give it a different feed partition.

---

## Use a simulator

To evaluate the platform without a live feed, add the `mf-eta-simulator` image - a synthetic ETA source that replays recorded content, so your projectors have something to serve.

| Image | Role | Release |
|-------|------|---------|
| `mf-eta-simulator` | Synthetic ETA data source | [`deploy-mf-eta-simulator`](https://github.com/MetaFluent-Dist-NN/deploy-mf-eta-simulator/releases/tag/MILESTONE-v6.0.0) |

The simulator *is* the ETA server, and on a single-host deployment it is already reachable at the `localhost` default - nothing to set.

Run it the same way as everything else: as another `./run` package, another Compose service, or another `Deployment`. For Docker, add this service to the file above:

```yaml
  mf-eta-simulator:
    image: ghcr.io/metafluent-dist-nn/mf-eta-simulator-cfg-stable:milestone
    container_name: mf-eta-simulator
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
```

---

## Going further

- [Fine-Grained](Cookbook-Deploy-Fine-Grained.md) - run each service separately for isolation and per-service redundancy.
- [Static MDS with Compute](Cookbook-Deploy-Static-Compute.md) - add a compute tier that derives computed content.
- [Scalable MDS](Cookbook-Deploy-Scalable.md) - let the projector tier grow and shrink with load automatically.
- High availability: run the core services as an active/standby pair - see [Architecture: Advanced](Architecture-Advanced.md#high-availability-activestandby) and [Deployment: Advanced](Deployment-Advanced.md).
- Serving real, entitled Refinitiv data? See [Configure DACS](Cookbook-Configure-DACS.md) to turn on authentication and entitlement checks.

---

## Where to go next

- [Confirm it's running](Operations-Monitoring.md#is-the-system-healthy) - check every component's health once the deployment is up.
- [Architecture: Advanced](Architecture-Advanced.md#fixed-capacity-multi-homed) - the topology this page deploys, and why.
- [Deployment: Without Docker](Deployment-Without-Docker.md) - the conventional install mechanics in full.
- [Image Catalog](Image-Catalog.md) - what each image contains.
- [Configuration: Basics](Configuration-Basics.md) - what the configuration you supply contains.
