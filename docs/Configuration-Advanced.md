# Configuration: Advanced

This builds on [Configuration: Basics](Configuration-Basics.md). Basics covers setting values and seeing what is in effect; this page is how a deployment's configuration is actually **assembled** - the switches, the per-component settings files it pulls in, environment-variable substitution, and the fuller ways to inspect it.

**Audience:** Operator, Architect.

---

## How a deployment's configuration is assembled

Every component ships with **self-contained defaults**, so in most cases it runs without configuration. A deployment adjusts those defaults through its **`deployment.properties`** - the operator entry point - and the per-component files it pulls in.

`deployment.properties` is kept short. It carries the **switches** and **required** values directly, and it pulls in one **settings file per component** through an `includePaths` list:

```
com.metafluent.blueprint.bootstrap.applicationConfig.includePaths=\
    $(METAFLUENT_CONFIG_OVERRIDES)/mf-session.properties,\
    $(METAFLUENT_DEPLOYMENT_CONFIG)/settings/com.metafluent.blueprint.rtc.session.server.tcpip.properties
```

The first entry is the image's own override layer, fixed by whoever built the image; the rest are the component settings files you edit. This list is generated - you change values in the settings files, not the include list itself.

The effective value of any property is therefore the shipped **default**, unless a switch, a required value, or a component's settings file overrides it. Each override is a literal value or an [environment-variable reference](#environment-variable-substitution) resolved at startup. The self-report shows the `default` and the resolved `actual` side by side, so you can see which won.

---

## Switches

Some choices are a single on/off decision rather than a value to tune - whether DACS authentication is active, which authorization provider a content adapter uses. These are **switches**, listed together at the top of `deployment.properties`. You set the value directly; there is nothing to include or swap.

For example, a session server either authenticates clients against DACS or accepts them unauthenticated:

```
com.metafluent.blueprint.rtc.session.server.tcpip.server.authenticationDomain=NO-AUTHN
```

The default is `NO-AUTHN`. To authenticate against DACS, set it to `DACS` and restart:

```
com.metafluent.blueprint.rtc.session.server.tcpip.server.authenticationDomain=DACS
```

A deployment typically has several switches - client authentication, whether a content adapter is disabled, and the like. Each is a plain value the component reads at startup, so its effect appears in the same self-report as any other property.

---

## Environment-variable substitution

So that one deployable image adapts to a deployment without editing files per machine, values may reference **environment variables**:

- `$(NAME)` - the value of `NAME`.
- `$(NAME:default)` - the value of `NAME`, or `default` if it is not set.
- `$(NAME:)` - the value of `NAME`, or empty if it is not set.

This is how host- and site-specific values - ports, hostnames, data directories, client networks - are threaded in from the deployment environment rather than hard-coded. For example, a setting may default to `$(METAFLUENT_CLIENT_NETWORKS:)`, taking the value of that environment variable, or empty if the deployment does not set it.

---

## Tokens

REST / management access control is **presence-based**: it is not a strictness switch you turn, but a consequence of what you provision on the **gateway node** (the only enforcement point). Provision nothing and the gateway serves openly - the default. Provision a **token store** and personal tokens are enforced (the "tokens only" posture). The concepts are in [Security: Advanced](Security-Advanced.md); this is what a deployment supplies.

**The store lives on the primary gateway.** The token store is the one piece of durable security state, so the primary gateway needs a writable persistent volume - `/app/data`, mounted the same way the resource-store images already mount it. Secondary gateways hold no store (they forward token checks to the primary), so they need no volume. Provisioning the store **without** mounting `/app/data` is a loud startup error, not a silent half-state.

**The first admin token comes from a first-boot secret.** On the first start with an empty data volume, the gateway generates a **one-time bootstrap secret** and prints it once to the deploy log (`/app/logs`). An admin uses it a single time to mint the first real admin token, after which it is retired; from then on that admin token issues everyone else's. The operator task flow is in [API Token Administration](API-Token-Administration.md). Wiping the data volume makes the next start a fresh first boot - the deliberate reset path.

**Tunables.** Token **expiry** defaults to 90 days; it is tunable up or down, and can be switched off entirely (tokens that never expire) for gentler sites. The validator's **switch-off delay** - how long a revoked token may still be accepted from the door's short-term memory - is also tunable (seconds to a minute).

**Applying it - two ways, one image.** The token config sits alongside the existing gateway on/off and DACS on/off choices, so it is the **same one image** either way:

- **As a deployment choice (default).** Supply the store config on the gateway service in the deployment - `deployment.properties` for a conventional install, `docker-compose.yml` for Docker, or the equivalent `$(ENV)` / mounted files on Kubernetes - and restart it. No rebake.
- **Baked into the image.** Freeze the provisioning into a `-cfg-<tag>` image (the same `--config-tag` freeze used for every other config choice) so it cannot be changed downstream - for example a bank shipping an image pinned to "tokens only".

The exact property names live in [Configuration: Reference](Configuration-Reference.md).

---

## Single sign-on (SSO)

The **full** posture adds company single sign-on on top of tokens: people are sent to their company login and then make their own tokens. It is provisioned by supplying the login doorway's configuration and certificates; with them absent, the deployment stays at "tokens only". The mechanism is described in [Security: Advanced](Security-Advanced.md).

**Operator files go under `resources/rest.sso/`.** The SAML configuration (its `SAML.properties` plus the service-provider keystore), the identity provider's certificate, the doorway's own signing keystore, and any customer-supplied certificates are operator files dropped into the deploy project's `deployment-config/resources/rest.sso/`, resolved at runtime via `METAFLUENT_CONFIG_RESOURCES`. (`rest.sso` is a deliberately short directory name - the one exception to the fully-qualified `<component>` naming the rest of the config surface uses, kept short because these paths are hand-edited and documented.) This is the one customer-editable area that survives upgrades. Files are bind-mounted live (visible on restart, no rebake) or frozen into a `-cfg-<tag>` image at bake. Keystore and certificate paths ship **empty by default** - must-supply-if-used.

**The SAML settings that matter:**

- **Service-provider entityID** - `MetaFluentJMS` by default. It is an identifier, not an endpoint, so keep the default unless you have a reason to change it: an existing identity-provider registration keeps matching on it even when the service moves host or port.
- **Identity-provider certificate** - supplied per deployment; the doorway verifies the signed assertion against it.
- **Role attribute** - the identity provider delivers `metafluent-admin` or `metafluent-guest`, which map to full and look-only access respectively.

**Gateway-side settings for SSO:**

- The gateway is configured with the **doorway's public signing certificate** so it can validate single sign-on access tokens offline, with no call back to the doorway.
- An **allowed-origins** list names the dashboard's origin(s) (development and production), since the dashboard calls the gateway cross-origin.

**The doorway and the gateway must agree on two values.** Single sign-on is configured on both sides - the doorway that issues access tokens and the gateway that verifies them - and two things have to match across them, or every single sign-on call is silently rejected:

- **Issuer and audience.** The doorway stamps an issuer and an audience onto each access token, and the gateway rejects any token whose issuer or audience is not the value it expects. Both default to `metafluent-sso` and `metafluent-gateway`, so at their defaults they already agree - change the gateway's expected value only if you change the doorway's.
- **The signing keypair.** The doorway signs tokens with its private key (its signing keystore); the gateway verifies them with the matching public certificate (the doorway's public signing certificate, above). They are one keypair - the certificate the gateway holds must be the public half of the doorway's keystore. A mismatched pair fails every verification.

---

## JVM memory and options

Every component starts with sensible JVM defaults, and in most deployments you leave them alone. When a component needs more memory, a different garbage collector, or a fixed number of processors, you tune it with `METAFLUENT_JVM_*` environment variables on that component. The launcher reads them each time the component starts and builds the JVM options from them, so the same settings work however you launch it: a Docker Compose `environment:` block, a Kubernetes `env:` list, or the environment of a host install.

### Defaults

With none of the variables set, the JVM sizes itself from the memory it can see - the container's memory limit if one is set, otherwise the host's memory. The maximum heap is then a quarter of that memory, and the heap grows from a small initial size as it is needed.

Change this when you want a component to use a larger share of its container, when you want the heap fixed at a known size so it never resizes, or when you run several components on one host and want each to stay within a budget. Components that carry many client subscriptions, such as projectors, are the ones most likely to need a larger share; small supporting services usually run well on the defaults.

### The variables

| Variable | Effect |
|----------|--------|
| `METAFLUENT_JVM_HEAP` | Heap size as a fixed amount, for example `384m` or `2g`. Sets the initial and maximum heap to the same value (`-Xms` and `-Xmx`), so the heap does not resize. Use it where the container has no memory limit, or where you want an exact size. Set this or `METAFLUENT_JVM_HEAP_PCT`, not both: a component given both does not start, and says so. |
| `METAFLUENT_JVM_HEAP_PCT` | Heap size as a percentage of the memory the container or JVM sees, for example `60`. Sets the initial and maximum heap to the same value (`-XX:InitialRAMPercentage` and `-XX:MaxRAMPercentage`), so the heap does not resize. Use it where the container has a memory limit. |
| `METAFLUENT_JVM_MAX_DIRECT` | Limit on direct (off-heap) memory, for example `512m` (`-XX:MaxDirectMemorySize`). |
| `METAFLUENT_JVM_GC` | Garbage collector: `zgc` or `g1`. Unset, or any other value, leaves the JVM default, which is G1. |
| `METAFLUENT_JVM_GC_PAUSE` | Pause-time goal in milliseconds for the G1 collector (`-XX:MaxGCPauseMillis`). |
| `METAFLUENT_JVM_PRETOUCH` | `true` commits all heap memory at start (`-XX:+AlwaysPreTouch`), so memory pressure shows at start-up instead of under load. Any other value leaves it off. |
| `METAFLUENT_JVM_ACTIVE_PROCS` | Number of processors the JVM sizes itself for (`-XX:ActiveProcessorCount`). |
| `METAFLUENT_JVM_EXTRA_OPTS` | Raw JVM flags, for example `-XX:+UseStringDeduplication`. Appended after the other options in every case. |
| `METAFLUENT_JVM_OPTS` | A complete replacement for the computed options, used verbatim. The other `METAFLUENT_JVM_*` tuning variables are then not applied, and the always-on flags below are yours to include. `METAFLUENT_JVM_EXTRA_OPTS` is still appended. |

These variables are the way to set JVM options. A component started with the `VM_OPTS` environment variable set does not start, and its message names the variable to use instead.

### How memory is divided

A component's memory has several parts: the **heap** (`METAFLUENT_JVM_HEAP` or `METAFLUENT_JVM_HEAP_PCT`), **direct memory** used for network and file buffers (`METAFLUENT_JVM_MAX_DIRECT`), and the JVM's own overhead for class metadata, thread stacks, compiled code and the collector's data structures. A container's memory limit has to cover all three. Set the heap to a share of the limit that leaves room for the rest; a heap near 100 percent of the limit leaves the JVM nothing for direct memory and overhead, and the container can then be stopped by the host for exceeding its limit.

The percentage applies to the memory the JVM sees. In a container with a memory limit that is the limit; on a host install it is the host's memory, so on a shared host prefer a fixed size such as `-Xmx` in `METAFLUENT_JVM_EXTRA_OPTS`.

### Always-on behaviour

Unless `METAFLUENT_JVM_OPTS` replaces the options, every component also runs with:

- **Exit on `OutOfMemoryError`** (`-XX:+ExitOnOutOfMemoryError`). The process stops at once so a standby or your orchestrator can recover, instead of running on in a degraded state.
- **A heap dump** (`-XX:+HeapDumpOnOutOfMemoryError`), written to the component's log directory as `java_pid<pid>.hprof`.
- **A GC log** (`-Xlog:gc*`), `gc-<component>.log` in the log directory, rotated across 5 files of 20 MB each. It is on all the time so a garbage-collection incident is still on record after a restart.

The log directory is `/app/logs` in a container (the compositions mount it as `./logs`) and `app/logs/` in an installation package. These are the files to collect when you investigate a component that restarted or a pause you want to explain; see [Operations: Troubleshooting & FAQ](Operations-Troubleshooting.md).

If you use `METAFLUENT_JVM_OPTS`, include these flags yourself to keep the behaviour:

```
-XX:+ExitOnOutOfMemoryError -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/app/logs
-Xlog:gc*:file=/app/logs/gc-<component>.log:uptime,level,tags:filecount=5,filesize=20m
```

### Where to set them

**Docker Compose.** Add the variables to the service's `environment:`, next to any other `METAFLUENT_*` settings:

```yaml
  mf-projector-mds:
    image: ghcr.io/metafluent-dist-nn/mf-projector-mds-cfg-stable:milestone
    mem_limit: 4g
    environment:
      METAFLUENT_JVM_HEAP_PCT: "60"
      METAFLUENT_JVM_MAX_DIRECT: "512m"
      METAFLUENT_JVM_GC: "zgc"
```

**Kubernetes and other launchers.** Pass the same variables as the container's environment - the `env:` list of a Kubernetes container, or `-e` on `docker run`.

**Without Docker.** Set the variables in the environment the `run` launcher starts in. With a `systemd` unit, use `Environment=` lines or an `EnvironmentFile=` (see [Deployment: Without Docker](Deployment-Without-Docker.md)). From a shell, a small file of `KEY=value` lines keeps the settings together with the install:

```
METAFLUENT_JVM_HEAP_PCT=40
METAFLUENT_JVM_MAX_DIRECT=256m
```

Save it as `jvm.env` and start with `set -a; . ./jvm.env; set +a; ./run`.

### Worked examples

**A memory-limited host, a fixed heap for each component.** On one host that runs several components, give each container a limit and a heap percentage that leaves headroom. Here each container is limited to 1 GB and its heap is fixed at about 600 MB:

```yaml
    mem_limit: 1g
    environment:
      METAFLUENT_JVM_HEAP_PCT: "60"
      METAFLUENT_JVM_MAX_DIRECT: "128m"
```

The heap is committed at its full size from the start and never resizes. The remaining 400 MB covers direct memory and the JVM's overhead. To pin a heap to an exact size instead of a percentage, use `METAFLUENT_JVM_HEAP: "384m"`.

**A projector with a larger share.** Give the projector a bigger container and a larger share of it for the heap, and leave the other services on their defaults:

```yaml
  mf-projector-mds:
    mem_limit: 8g
    environment:
      METAFLUENT_JVM_HEAP_PCT: "65"
      METAFLUENT_JVM_MAX_DIRECT: "1g"
      METAFLUENT_JVM_GC: "zgc"
```

The heap is about 5.2 GB, direct memory is capped at 1 GB, and the rest of the 8 GB covers the JVM's overhead. To check the effect, read the container's `memoryUsedPercent` as described in [Operations: Monitoring & Diagnostics](Operations-Monitoring.md#resource-monitoring).

---

## Inspecting the effective configuration in depth

[Configuration: Basics](Configuration-Basics.md) covers the two on-disk reports and the quick "what did I change" extraction. Going deeper, the `config` API answers two questions live over the gateway.

**Each effective property, with its default.** `fullProperties` returns *all* properties in effect - not only the ones you changed - each with its `default` and resolved `actual`:

```
curl -s "http://mf-api-gateway:9090/api/config/v1/*/fullProperties?bundleName=.*"
```
```json
[ { "bundleName": "com.metafluent.blueprint.rtc.session.server.tcpip", "bundleVersion": "6.3.0",
    "properties": [
      { "name": "server.default",   "default": "8900", "actual": "8900" },
      { "name": "server.authenticationDomain", "default": "NO-AUTHN", "actual": "DACS" } ] } ]
```

The `default` vs `actual` pairing is the point: it tells you what each property resolved to and, at a glance, which ones differ from their shipped value.

**Narrow by component.** `bundleName` is a regex, so you can focus on one area:

```
curl -s "http://mf-api-gateway:9090/api/config/v1/*/fullProperties?bundleName=com.metafluent.blueprint.rtc.session.*"
```

**Narrow by container.** On a multi-container deployment, select one container's configuration with the `image=` predicate:

```
curl -s "http://mf-api-gateway:9090/api/config/v1/image=mf-mds-consolidated/fullProperties?bundleName=.*"
```

For only the properties that differ from their defaults, use `allModifiedProperties` in place of `fullProperties` (see [Configuration: Basics](Configuration-Basics.md)).

---

## Where to go next

- [Configuration: Basics](Configuration-Basics.md) - setting values and the configuration reports.
- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - watching a container's memory.
- [Deployment: Basics](Deployment-Basics.md) - where `deployment.properties` lives and how a deployment is built.
- [Access Control](Access-Control.md) - the client-authentication switch this page's example sets.
- [Security: Advanced](Security-Advanced.md) - the concepts behind the Tokens and single sign-on sections above.
- [API Token Administration](API-Token-Administration.md) - the operator flow for issuing and managing tokens.
- [REST API](REST-API.md) - the query grammar behind the `config` calls.
