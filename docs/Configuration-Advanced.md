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
- [Deployment: Basics](Deployment-Basics.md) - where `deployment.properties` lives and how a deployment is built.
- [Access Control](Access-Control.md) - the client-authentication switch this page's example sets.
- [Security: Advanced](Security-Advanced.md) - the concepts behind the Tokens and single sign-on sections above.
- [API Token Administration](API-Token-Administration.md) - the operator flow for issuing and managing tokens.
- [REST API](REST-API.md) - the query grammar behind the `config` calls.
