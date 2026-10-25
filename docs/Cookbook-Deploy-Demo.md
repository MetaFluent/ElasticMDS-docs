# Deployment Cookbook: Demo

The fastest way to see Elastic MDS running: one image with the entire system inside, plus a simulator to feed it. This greatly simplified setup could run on a laptop or a single lab machine - it is built to get you to a working result quickly, not to lay out a production deployment.

**Audience:** anyone evaluating Elastic MDS. Start here to see the platform working, then move to [Static MDS](Cookbook-Deploy-Static-MDS.md) when you are ready for a real deployment.

This is the **Consolidated** topology in [Architecture: Advanced](Architecture-Advanced.md#consolidated) - read that for the full picture; install here first and learn the details later.

---

## The two images, two ways to run them

| Method | You launch it with | Ideal for |
|--------|--------------------|-----------|
| **Conventional** | the host `./run` launcher | running natively without Docker |
| **Docker** | `docker compose up` | the quickest way to get going, on a laptop or a single lab machine |

---

## Images you need

| Image | Role | Release |
|-------|------|---------|
| `mf-mds-consolidated` | A complete market-data server in one image: session, SQL, pub/sub, push/refresh, orchestration, entitlements, config storage, and the ETA/MAMA adapters | [`deploy-mf-mds-consolidated`](https://github.com/MetaFluent-Dist-NN/deploy-mf-mds-consolidated/releases/tag/MILESTONE-v6.0.0) |
| `mf-eta-simulator` | Synthetic ETA data source that replays recorded content, so the system has something to serve without a live feed | [`deploy-mf-eta-simulator`](https://github.com/MetaFluent-Dist-NN/deploy-mf-eta-simulator/releases/tag/MILESTONE-v6.0.0) |

See the [Image Catalog](Image-Catalog.md) for what each image contains.

---

## Conventional Demo

1. From each release above, download the installation-package zip and unpack it.
2. Set `JAVA_HOME` and start each with `./run`, one per terminal (or backgrounded).

Each service looks for the gateway at `mf-api-gateway:9090` by default. Point it at your gateway host whatever way suits you - set `METAFLUENT_API_GATEWAY_HOST` in the launch environment, or map the name in your own name resolution. On a single machine, both are just as easy.

**Point `mf-mds-consolidated` at its ETA server.** The ETA/MDS adapter's `manager.etaServerHost` defaults to `localhost` on port `14002` - since the simulator runs on the same machine in this demo, there is nothing to set.

---

## Docker Demo

Docker Compose brings both up on a single machine with one command.

Save this as `docker-compose.yml` and run `METAFLUENT_HOST_UID=$(id -u) docker compose up -d`:

```yaml
services:

  mf-mds-consolidated:
    image: ghcr.io/metafluent-dist-nn/mf-mds-consolidated-cfg-stable:milestone
    container_name: mf-mds-consolidated
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_MAMA_DISABLED: "true"   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

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

`METAFLUENT_HOST_UID` gives the in-container user your host UID, so the bind-mounted `./logs` and `./data` stay writable.

---

## Where to go next

- [Confirm it's running](Operations-Monitoring.md#is-the-system-healthy) - check every component's health once the deployment is up.
- [Static MDS](Cookbook-Deploy-Static-MDS.md) - the next step toward a real deployment: the core services and a projector pool you size yourself.
- [Architecture: Basics](Architecture-Basics.md) - the mental model behind what you just ran.
- [Image Catalog](Image-Catalog.md) - what each image contains.
