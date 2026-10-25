# Security: Basics

Elastic MDS's security is best understood as a set of distinct **surfaces**, each secured on its own terms. This page covers the **operational** surfaces - administrative / REST access, cluster-internal traffic, transport, and deployment secrets. How applications prove who they are and what content they may see - client authentication and entitlements - is covered separately in **[Access Control](Access-Control.md)**. The mechanisms behind these surfaces - how personal tokens work, the machine-to-machine channel, and single sign-on - are in **[Security: Advanced](Security-Advanced.md)**.

**Audience:** Architect, Operator.

---

## Administrative and REST access

The REST **control plane** - the gateway surface that reads state and statistics and controls runtime settings (see [REST API](REST-API.md)) - is authenticated with **API tokens**. This is the management plane; client access to market data is governed by client authentication and entitlements (see [Access Control](Access-Control.md)).

**Using a token.** A caller presents its token as a bearer credential on each REST call, and the gateway validates it before serving the request; every endpoint requires one:

```
Authorization: Bearer mft_...
```

**Permissions (scopes).** Most deployments use two levels:

- **read-only** (`*:read`) - read all state and statistics, change nothing.
- **full** (`*:*`) - read and control.

For finer control, a token can be scoped to a specific area and action - for example, a token allowed only to raise logging levels - with a scope of the form `<api>[.<object>]:<action>`. Scopes derive from the existing API structure, so there is nothing to configure per endpoint.

**Issuing and managing tokens.** Tokens are **operator-issued**, one per person or automation, per cluster. The value is shown **once** when the token is minted and stored only as a hash - it cannot be recovered, only reissued - and an operator can grant only the access they themselves hold; tokens carry an expiry. Issuing, granting, revoking, and the single sign-on login are done through the token administration interface, hosted by the API Gateway - see **[API Token Administration](API-Token-Administration.md)**.

---

## Cluster-internal access

Nodes also communicate with each other - registration, keep-alive, and internal lookups pass between a node and the API Gateway on a **separate internal channel**, kept apart from the client-facing and REST surfaces. Traffic on this channel is authenticated with a **cluster machine secret**: a single value that every node holds an identical copy of. A node presents it on each internal request, and the gateway verifies it.

The internal channel follows the same presence-based rule as the token surface: where the machine secret is provisioned, the channel **requires** it; where it is absent, the channel is open. Provisioning the secret is the act that turns cluster-internal authentication on.

A node whose machine secret is missing, or does not match the cluster, is refused on the internal channel and reports itself as **non-functional** rather than run half-authenticated - a misconfiguration fails visibly (see [Operations: Monitoring](Operations-Monitoring.md)).

### Provisioning the machine secret

The machine secret is generated **once for the whole cluster**, and the same value is placed on **every** node. Generate it from the `deploy-mf-api-gateway` deployment, giving it the file to write - by default `./data/security/machine/machine.secret` (`./data` is the node's data directory, which the gateway reads as `$(METAFLUENT_DATA_DIR)/security/machine/machine.secret`):

```bash
cd deploy-mf-api-gateway
scripts/generate-machine-secret ./data/security/machine/machine.secret
```

The secret is written to that file and printed once. The tool refuses to overwrite an existing secret, since the value is cluster-wide and generated only once. If your deployment keeps its data directory elsewhere, give that path instead - see [Configuration: Reference](Configuration-Reference.md).

Put that **same** value at `security/machine/machine.secret` under every other node's data directory, before the node starts:

- **Kubernetes** - one Secret, mounted into every pod at that path.
- **File-based** - copy the value to each node's data directory (see [Deployment: Without Docker](Deployment-Without-Docker.md)).

Do not run the generator per node: a second run produces a different value, and a node holding the wrong value cannot join. Rotating the secret is an all-nodes operation - generate a new value, distribute it everywhere, and restart the cluster.

A site that manages its own secrets can place its own value at the same path instead.

---

## Transport security

Within a deployment the services communicate over the deployment's trusted networks (see [Deployment: Basics](Deployment-Basics.md)). TLS for the REST/control plane is being added; until then, keep the gateway on a trusted management network and off client-facing ones.

---

## Deployment secrets

Some deployment settings are genuine secrets - for example the **database username and password** a content adapter uses to connect to its source, such as the RDBMS adapter's JDBC credentials. Secrets like these are supplied through the deployment's configuration and environment variables, and must be kept **out of source control**. The **cluster machine secret** (see [Cluster-internal access](#cluster-internal-access)) is another such secret. See [Configuration: Basics](Configuration-Basics.md) and [Deployment: Basics](Deployment-Basics.md).

---

## Related pages

- [Security: Advanced](Security-Advanced.md) - the mechanisms behind these surfaces: the token model, the machine door, and single sign-on.
- [Access Control](Access-Control.md) - client authentication and the entitlements (authorization) framework.
- [API Token Administration](API-Token-Administration.md) - issuing and managing REST tokens.
- [Deployment: Basics](Deployment-Basics.md) - network placement of the gateway.
- [REST API](REST-API.md) - the control plane these protections apply to.
