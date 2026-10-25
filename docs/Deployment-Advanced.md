# Deployment: Advanced

[Deployment: Basics](Deployment-Basics.md) gets a deployment running. This page is about the part that decides whether clients can actually reach it: **networking** - how each server chooses what to listen on and what address to hand a client, and how the deployment topologies (from a laptop to Kubernetes) follow from a few choices.

The good news up front: **you choose how much networking you take on, and the simple choice is a first-class one.** Most deployments never touch anything on this page.

**Audience:** Architect, Operator.

---

## Bind vs advertise

A server has to answer two questions that sound the same but are not:

- **Bind** - which local interface(s) do I listen on?
- **Advertise** - what address do I hand a remote client so it can connect back to me?

They diverge the moment a server has more than one address, or an address that is not directly reachable from where the client sits - a Docker bridge IP, a Kubernetes pod behind a Service, a cloud instance behind NAT. A server can listen on every interface it owns and still have to tell each client one *specific, routable-from-that-client* address. Getting bind right is easy; getting advertise right is the whole game.

Elastic MDS resolves a host at **three** separate moments:

| Moment | Question | Resolved from |
|--------|----------|---------------|
| **Bind** | Which interface do I listen on? | All interfaces when no networks are configured; otherwise one bound socket per network, on the interface whose IP is in that network's range. |
| **Client advertise** | What address goes in the metadata a client reads? | That network's **advertise host**, if you set one; otherwise the bound interface's IP on that network. |
| **Mesh discover** | What address do peer *nodes* use to reach me? | Always the bound control-network IP - peers are inside the cluster, so the raw address is correct. |

### There is no single "public host"

A server on three networks has three addresses, each routable only from its own network. There is no one address that is "the" public host - the correct address to advertise depends entirely on **which network the client is on**. That is why advertisement is resolved **per network**. The only case where a single global address is meaningful is a flat, unsegmented deployment, and there the bound interface IP already fills the role.

---

## Flat vs segmented

There are two modes, and most deployments want the first.

- **Flat (unsegmented).** Configure no networks at all: every server binds all of its interfaces and hands each client the single address it has. This is the **default** - no descriptors, no per-network addresses, nothing to reason about. It is the right choice for development, a conventional single-host install, single-network Docker, and any deployment where clients and servers share one reachable network.
- **Segmented (multi-homed).** For when one flat network is not enough - you want to keep control-plane traffic off the client network, serve distinct client populations on separate networks, or advertise a different (externally routable) address per network. You **name** logical networks, and the platform resolves each to its own bind interface and advertised address.

Segmentation is **opt-in**: it engages only when you set the `*_NETWORKS` variables. Set nothing and the cluster runs flat and wide-open. Reach for segmentation only when a concrete requirement - isolation, multiple client networks, external routability - asks for it.

Segmentation is also more than plumbing: because orchestration delivers content only where a client can reach it, network boundaries become **isolation and cost boundaries** around a business unit. See [Isolating access by deployment topology](Architecture-Advanced.md#isolating-access-by-deployment-topology) for the model; this page is how you build it.

---

## Segmenting a deployment

Three things drive segmented networking.

**1. The network variables.** Each names one or more logical networks:

| Variable | Applies to |
|----------|-----------|
| `METAFLUENT_CLIENT_NETWORKS` | The client-facing servers (push / refresh / session / sql / pubsub). Unset = bind all interfaces. |
| `METAFLUENT_PRIVATE_NETWORKS` | Private tier-to-tier traffic (for example, projector to core). |
| `METAFLUENT_CONTROL_NETWORKS` | The DataFabric mesh (node-to-node replication) and the gateway's own advertised address. Set on **every** container in a segmented deployment. |

**2. The network descriptor.** A JSON descriptor, authored once, defines each logical network:

| Field | Purpose |
|-------|---------|
| `Name` | The logical name referenced by the `*_NETWORKS` variables. |
| `Cidr` | The subnet, used to pick the bind interface (the one whose address is inside this range). |
| `AdvertiseHost` | *Optional.* The address to hand clients on this network. Omit it to advertise the bound interface IP. **Set it when the bound IP is not reachable from the client** - off-host, a cloud NAT/public address, a Kubernetes LoadBalancer. |

`AdvertiseHost` is the load-bearing field: it is exactly how you hand an external client an address it can actually reach when the server's own interface IP is private.

**3. Fail-loud.** If a configured network name is unknown, or the descriptor is missing while names are set, startup **fails loudly** - there is no silent fall back to wide-open binding. A segmented deployment that misconfigures a network stops, rather than quietly serving unreachable addresses.

---

## The API gateway is separate

The gateway does not use the data-server transport; it has its own, simpler host model:

- It **binds** all interfaces on its REST port, and advertises its **control-network** address (or, unsegmented, its own host address).
- The **central** ("standalone") gateway binds `METAFLUENT_API_GATEWAY_PORT` (default `9090`); a port conflict there is fatal. Every other node runs a **container-local** gateway that registers its endpoints with the central one and is told where the central gateway is via `METAFLUENT_API_GATEWAY_HOST` / `_PORT`.
- The central gateway **proxies** each backend at the literal `host:port` that backend reported when it registered - so a backend's advertised address must be reachable from the gateway (the control network).
- **Public exposure is an ingress concern.** The gateway never encodes its own public hostname; expose port `9090` through whatever ingress / Service / load-balancer the platform provides. Keep it on a management network, not a client-facing one (see [Security: Basics](Security-Basics.md)).

---

## Deployment topologies

The same service catalog runs in all of them (see the topology diagrams in [Architecture: Advanced](Architecture-Advanced.md)); what changes is the networking. Conventional, Docker, and Kubernetes are peer run methods - the conventional host install is the primary path; compositions are **worked templates** for Docker; **Kubernetes is the production substrate** at scale.

**Conventional (host install).** No container, no network namespace to cross - each process binds directly on the host's own interfaces. Wildcard bind; the bound IP *is* the host IP, reachable by external clients at the host's address, the same as Docker host networking below. Nothing to set for a single-host or local-client deployment; no `METAFLUENT_HOST_UID`, no logical networks required. See [Deployment: Without Docker](Deployment-Without-Docker.md) for the install mechanics.

**Docker, host networking** (`consolidated`, `scalable`, `static`). Containers share the host stack; wildcard bind; the bound IP *is* the host IP, reachable by external clients at the host's address. Requires `METAFLUENT_HOST_UID`; no logical networks.

**Docker, bridged single-network** (`consolidated-bridged`, `scalable-bridged`). One Docker bridge; the advertised address is the container's **bridge IP**, reachable **only from sibling containers on the same bridge** (by service name). Run clients as siblings; off-host clients need published ports or a different topology.

**Docker, macvlan / multihomed-bridged** (`scalable-multihomed-bridged`, `fine-grained-multihomed-bridged`). The reference for segmentation: distinct `control` / `client-a` / `client-b` / `external` networks, each server bound and advertised per network. **macvlan** puts containers directly on the physical LAN, so off-host clients on the same L2 reach them without published ports. Author a descriptor with a `Cidr` per network; set `AdvertiseHost` only where the bound IP is not client-routable.

**Kubernetes** (production). Two cases:
- *Gateway is the only public entry.* Data servers stay in-cluster (pod IPs); expose only the gateway's `9090` via a `Service` / `Ingress`. Set `METAFLUENT_CONTROL_NETWORKS` so backends register a control-network address the gateway can reach.
- *External clients open data connections* (push / refresh / pubsub), not just the gateway. The pod IP is unreachable from outside, so this **must** be segmented: give the client-facing network an `AdvertiseHost` of the external endpoint (NodePort / LoadBalancer / external DNS). This is the canonical advertise-host case.

---

## Quick decision guide

- **Clients local or same-host?** Wildcard bind; the bound IP is fine.
- **Clients are sibling containers on one bridge?** Wildcard bind; the bridge IP; connect by service name.
- **Multiple client populations, off-host, cloud, or Kubernetes-external?** Segment with `*_NETWORKS`, author a descriptor, and set `AdvertiseHost` on any network whose bound IP is not client-routable.
- **Only the gateway is public?** Expose `9090` through ingress; keep the data servers internal.

---

## Where to go next

- [Deployment: Basics](Deployment-Basics.md) - deployment projects, base images, and running a composition.
- [Architecture: Advanced](Architecture-Advanced.md) - the topology diagrams these correspond to.
- [Configuration: Advanced](Configuration-Advanced.md) - the `$(...)` environment substitution behind the network variables.
- [Security: Basics](Security-Basics.md) - keeping the gateway on a management network.
- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - confirming reachability on a running system.
