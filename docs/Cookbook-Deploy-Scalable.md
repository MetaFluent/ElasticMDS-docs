# Deployment Cookbook: Scalable MDS

The projector tier **grows and shrinks with load automatically**. Instead of sizing projectors by hand, you set a policy and the platform adds projectors when sustained load rises and retires them when it falls. A **container manager** starts and stops them on the underlying platform, so this deployment runs on Docker or Kubernetes.

**Audience:** Architect, Operator. Choose this when load is elastic and you want capacity to track demand.

This is the **Scalable, multi-homed** topology in [Architecture: Advanced](Architecture-Advanced.md#scalable-multi-homed) - read that for the full picture; install here first and learn the details later.

---

## The same images, run by a container manager

The core and projector images are the **same** as every other deployment. Scaling adds two things: the orchestration coordinator (already inside `mf-core-srvcs`) makes the scale decisions, and a **container manager** carries them out. Which container manager you use is the choice between the two methods:

| Method | Container manager | Ideal for |
|--------|-------------------|-----------|
| **Docker** | `mf-dcm` (Docker Container Manager) | development and lab |
| **Kubernetes** | `mf-k8s-cm` (Kubernetes Container Manager) | production |

`mf-k8s-cm` operates against the Kubernetes API with no host daemon access, which suits regulated, security-reviewed environments.

---

## Images you need

| Image | Role | Release |
|-------|------|---------|
| `mf-api-gateway` | REST entry point for the cluster | [`deploy-mf-api-gateway`](https://github.com/MetaFluent-Dist-NN/deploy-mf-api-gateway/releases/tag/MILESTONE-v6.0.0) |
| `mf-admin` | ResourceStore (config), network registry, central log | [`deploy-mf-admin`](https://github.com/MetaFluent-Dist-NN/deploy-mf-admin/releases/tag/MILESTONE-v6.0.0) |
| `mf-core-srvcs` | Session, SQL, pub/sub, and orchestration in one container | [`deploy-mf-core-srvcs`](https://github.com/MetaFluent-Dist-NN/deploy-mf-core-srvcs/releases/tag/MILESTONE-v6.0.0) |
| `mf-projector-mds` | MDS projector; the tier that scales | [`deploy-mf-projector-mds`](https://github.com/MetaFluent-Dist-NN/deploy-mf-projector-mds/releases/tag/MILESTONE-v6.0.0) |
| `mf-projector-compute` | Compute tier; scales alongside the MDS tier | `deploy-mf-projector-compute` |
| `mf-dcm` _(Docker)_ | Carries out scale decisions on Docker | `deploy-mf-dcm` |
| `mf-k8s-cm` _(Kubernetes)_ | Carries out scale decisions on Kubernetes | `deploy-mf-k8s-cm` |

See the [Image Catalog](Image-Catalog.md) for what each image contains. To try the platform without a live feed, add a simulator - see [Use a simulator](#use-a-simulator) below.

**Point the projector at its ETA server.** The ETA/MDS projector reads its feed from an ETA server given by `manager.etaServerHost` (port `etaServerPort`, default `14002`). It defaults to `localhost`, so a feed on the same host needs nothing set. For a feed on another host, set `METAFLUENT_ETA_SERVER_HOST` on `mf-projector-mds` in the compose file (or the equivalent Kubernetes env) - the container manager launches every scaled instance from that same definition, so one setting covers them all.

---

## Docker Scalable

`mf-dcm` reads the Compose file, then starts and scales the projector services tagged `mf.scalable=true`. The management plane (gateway, admin, core services, dcm) starts with `docker compose up`; dcm launches and scales the projectors from there.

Save this as `docker-compose.yml`:

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

  mf-core-srvcs:
    image: ghcr.io/metafluent-dist-nn/mf-core-srvcs-cfg-stable:milestone
    container_name: mf-core-srvcs
    network_mode: host
    environment: { METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}" }
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-dcm:
    image: ghcr.io/metafluent-dist-nn/mf-dcm-cfg-stable:milestone
    container_name: mf-dcm
    network_mode: host
    working_dir: ${PWD}
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_COMPOSE_FILE: "${PWD}/docker-compose.yml"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ${PWD}:${PWD}:ro                       # dcm reads this compose file
      - /var/run/docker.sock:/var/run/docker.sock   # dcm drives the host daemon

  # Scalable tiers: dcm starts and scales these; they are profile-gated so
  # `docker compose up` leaves them to dcm.
  mf-projector-mds:
    image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
    network_mode: host
    profiles: ["scalable"]
    labels: { mf.scalable: "true" }
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_MAMA_DISABLED: "true"   # ETA feeds only; for MAMA see Deployment: Basics, MAMA feeds
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]

  mf-projector-compute:
    image: ghcr.io/metafluent-dist-nn/mf-projector-compute-cfg-stable:milestone
    network_mode: host
    profiles: ["scalable"]
    labels: { mf.scalable: "true" }
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_PUBSUB_ADAPTER_CONNECTION: "mf-session:8900"
    volumes: [ "./logs:/app/logs", "./data:/app/data" ]
```

Bring it up:

```
docker login ghcr.io                                  # first run: read:packages token
docker compose --profile scalable pull                # cache every image, including the scalable tiers
METAFLUENT_HOST_UID=$(id -u) docker compose up -d      # management plane starts; dcm scales the projectors
```

The first-run `pull` caches the projector images with your credentials, so dcm finds them locally when it scales.

---

## Kubernetes Scalable

The production deployment. `mf-k8s-cm` runs against the Kubernetes API and creates or removes projector pods as orchestration decides. It needs a ServiceAccount with permission to manage pods in its namespace.

The gateway, admin, and core services are deployed as in [Static MDS](Cookbook-Deploy-Static-MDS.md#kubernetes-static-mds). Add the container manager and its access:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: mf-k8s-cm }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: mf-k8s-cm }
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "create", "delete"]
  - apiGroups: [""]
    resources: ["pods/status"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: mf-k8s-cm }
subjects: [ { kind: ServiceAccount, name: mf-k8s-cm } ]
roleRef: { kind: Role, name: mf-k8s-cm, apiGroup: rbac.authorization.k8s.io }
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-k8s-cm }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-k8s-cm } }
  template:
    metadata: { labels: { app: mf-k8s-cm } }
    spec:
      serviceAccountName: mf-k8s-cm
      containers:
        - name: mf-k8s-cm
          image: ghcr.io/metafluent-dist-nn/mf-k8s-cm-cfg-stable:milestone
```

Orchestration (in `mf-core-srvcs`) drives the scaling; `mf-k8s-cm` creates and removes the `mf-projector-mds` and `mf-projector-compute` pods to match. Set the target namespace and ServiceAccount in the manager's `deployment-config/`.

---

## Use a simulator

To evaluate the platform without a live feed, add the `mf-eta-simulator` image, as in [Static MDS](Cookbook-Deploy-Static-MDS.md#use-a-simulator). The scalable MDS projectors source from it and the compute tier derives from what they serve.

---

## Going further

- [Static MDS](Cookbook-Deploy-Static-MDS.md) - the fixed-capacity starting point.
- [Fine-Grained](Cookbook-Deploy-Fine-Grained.md) - run each service separately.
- [Static MDS with Compute](Cookbook-Deploy-Static-Compute.md) - a fixed compute tier.
- High availability: run the core services as an active/standby pair alongside scaling - see [Architecture: Advanced](Architecture-Advanced.md#high-availability-activestandby).
- Serving real, entitled Refinitiv data? See [Configure DACS](Cookbook-Configure-DACS.md) to turn on authentication and entitlement checks.

---

## Where to go next

- [Confirm it's running](Operations-Monitoring.md#is-the-system-healthy) - check every component's health once the deployment is up.
- [Architecture: Advanced](Architecture-Advanced.md#auto-scaling) - how scaling decides, and the scaling policy.
- [Deployment: Advanced](Deployment-Advanced.md) - running the scalable topologies.
- [Image Catalog](Image-Catalog.md) - what each image contains.
- [Configuration: Basics](Configuration-Basics.md) - what the configuration you supply contains.
