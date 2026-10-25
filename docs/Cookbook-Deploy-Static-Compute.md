# Deployment Cookbook: Static MDS with Compute

[Static MDS](Cookbook-Deploy-Static-MDS.md) plus a **compute tier** - a projector that derives computed and interpolated content from what the other projectors serve, rather than sourcing an external feed. Add it when you want the platform to produce derived content: computed columns, curve interpolation, and functions from its computation libraries.

**Audience:** Architect, Operator. Start from Static MDS; this page adds one image.

The compute tier is the projector tier used as a **compute node**, described in [Architecture: Advanced](Architecture-Advanced.md#a-cost-boundary-too).

---

## The same images, three ways to run them

This is the Static MDS deployment with one image added, `mf-projector-compute`. Everything from [Static MDS](Cookbook-Deploy-Static-MDS.md) applies unchanged, including [how its MDS projectors find their ETA server](Cookbook-Deploy-Static-MDS.md#conventional-static-mds); below is the delta.

| Method | You launch it with | Ideal for |
|--------|--------------------|-----------|
| **Conventional** | the host `./run` launcher | the standard install - this is the primary path |
| **Docker** | `docker compose up` | a demo or lab on a single machine |
| **Kubernetes** | standard `Deployment` / `Service` manifests | a cluster-managed fixed install |

---

## The image you add

| Image | Role | Release |
|-------|------|---------|
| `mf-projector-compute` | Derives computed and interpolated content from other projectors' output | `deploy-mf-projector-compute` |

It joins the [Static MDS images](Cookbook-Deploy-Static-MDS.md#images-you-need): gateway, admin, core services, and one or more MDS projectors.

The compute projector hosts **computation libraries**. `intrinsic` (the SQL arithmetic and comparison operators) is always present; `basic`, `math`, and `interpolation` are available, with more to come. See the [Image Catalog](Image-Catalog.md#computed-content) for what each library provides.

---

## Conventional Static MDS with Compute

Install exactly as [Static MDS](Cookbook-Deploy-Static-MDS.md#conventional-static-mds), then add one more package:

1. Download and unpack the `mf-projector-compute` release above.
2. Edit its `deployment-config/` for your environment. Point it at the pub/sub service so it can source the content it computes from - `METAFLUENT_PUBSUB_ADAPTER_CONNECTION=mf-session:8900`, or the equivalent in `deployment-config/`.
3. Set `JAVA_HOME` and start it with `./run`.

Run more than one compute projector the same way when you want more computation throughput or resilience.

---

## Docker Static MDS with Compute

Take the [Static MDS Compose file](Cookbook-Deploy-Static-MDS.md#docker-static-mds) and add this service:

```yaml
  mf-projector-compute:
    image: ghcr.io/metafluent-dist-nn/mf-projector-compute-cfg-stable:milestone
    container_name: mf-projector-compute
    network_mode: host
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
      METAFLUENT_PUBSUB_ADAPTER_CONNECTION: "mf-session:8900"   # where it sources content to compute from
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
```

Bring it up with the rest: `METAFLUENT_HOST_UID=$(id -u) docker compose up -d`.

---

## Kubernetes Static MDS with Compute

An example. Add this to the [Static MDS manifests](Cookbook-Deploy-Static-MDS.md#kubernetes-static-mds):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-projector-compute }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-projector-compute } }
  template:
    metadata: { labels: { app: mf-projector-compute } }
    spec:
      containers:
        - name: mf-projector-compute
          image: ghcr.io/metafluent-dist-nn/mf-projector-compute-cfg-stable:milestone
          env:
            - { name: METAFLUENT_PUBSUB_ADAPTER_CONNECTION, value: "mf-session:8900" }
```

Raise `replicas`, or add another `Deployment`, for more computation throughput or resilience.

---

## Use a simulator

The same as [Static MDS](Cookbook-Deploy-Static-MDS.md#use-a-simulator) - add the `mf-eta-simulator` image to feed the MDS projectors, and the compute tier derives its content from what they serve.

---

## Going further

- [Static MDS](Cookbook-Deploy-Static-MDS.md) - the base deployment this extends.
- [Fine-Grained](Cookbook-Deploy-Fine-Grained.md) - run each service separately.
- [Scalable MDS](Cookbook-Deploy-Scalable.md) - let the projector and compute tiers grow and shrink with load automatically.
- Serving real, entitled Refinitiv data? See [Configure DACS](Cookbook-Configure-DACS.md) to turn on authentication and entitlement checks.

---

## Where to go next

- [Confirm it's running](Operations-Monitoring.md#is-the-system-healthy) - check every component's health once the deployment is up.
- [Architecture: Advanced](Architecture-Advanced.md#a-cost-boundary-too) - the projector tier as a compute node.
- [Image Catalog](Image-Catalog.md#computed-content) - the compute image and its libraries.
- [Deployment: Without Docker](Deployment-Without-Docker.md) - the conventional install mechanics in full.
- [Configuration: Basics](Configuration-Basics.md) - what the configuration you supply contains.
