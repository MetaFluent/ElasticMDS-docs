# Configuration Cookbook: Configure DACS

DACS - Refinitiv's Data Access Control System - authenticates client sessions and checks their entitlements against the feed. A deployment serving real, entitled Refinitiv (ETA / Elektron / BPIPE) market data will usually turn it on. This is the ordered task; the settings themselves live under `settings/`, with each one documented in its companion reference file.

**Audience:** Operator running real Refinitiv (ETA / Elektron / BPIPE) market data.
**Prerequisites:** a running deployment with a market-data projector, and a reachable DACS daemon (or daemon pair) for your entitlement environment.

---

## Before you start

- DACS ships **off** by default.
- It applies to any ETA/MDS-bearing deployment - `deploy-mf-projector-mds`, `deploy-mf-projector-eta`, or `deploy-mf-mds-consolidated` - under the generic project name `deploy-mf-<xxx>` below. The property names are identical in each; only the project you edit changes.
- Three files, all under `deploy-mf-<xxx>/deployment-config/`:
  - **`deployment.properties`** - the entry point; the two switches below live here.
  - **`settings/com.metafluent.blueprint.authnz.dacs.properties`** - the rest of DACS's settings.
  - **`settings/com.metafluent.blueprint.authnz.dacs-reference.txt`** - the full reference for every one of them.

---

## Steps

1. **Turn DACS on.** It ships disabled. This is the switch as it ships in `deployment.properties`:

   ```
   ################################################################
   # SWITCHES - on/off decisions for this deployment.
   # Full docs: the matching settings/<bundle>-reference.txt
   ################################################################

   # === com.metafluent.blueprint.authnz.dacs:6.3.0 ===

   ######################
   # Disable the DACS authentication/authorization controller.
   com.metafluent.blueprint.authnz.dacs.dacsAuthnz.disabled=true
   ```

   Set it to `false`.

2. **Point it at your DACS daemon.** This is the property as it ships in `deployment.properties`:

   ```
   # === com.metafluent.blueprint.authnz.dacs:6.3.0 ===

   ######################
   # Location of the DACS daemon in host:port[,host:port] format.
   com.metafluent.blueprint.authnz.dacs.dacsAuthnz.daemonLocation=
   ```

   Set it to your DACS daemon's `host:port`. For failover, list a second daemon comma-separated: `host1:port1,host2:port2`.

3. **Fine-tune it (optional).** Usage logging, user-name lower-casing, DACS On Demand, and the rest of DACS's behavior live in `settings/com.metafluent.blueprint.authnz.dacs.properties`. Every setting there is fully documented in the companion `settings/com.metafluent.blueprint.authnz.dacs-reference.txt` - read that file for the full option set before changing anything beyond the two switches above.

---

## Verify

Ask the gateway for the DACS controller on every MDS projector. `~` is a **like** (pattern) operator, so `container.image~mds` matches every MDS projector image variant - `mf-projector-mds`, its feed-split variants, and `mf-mds-consolidated` alike:

```
curl -s "http://mf-api-gateway:9090/api/application-state/v1/container.image~mds/constituents/name~DACSAuthnzDomainController/name,state,info"
```

A deployment with DACS enabled responds like this - one inner array per matching projector, each showing the controller `FULLY_OPERATIONAL`:

```json
[
    [ { "name": "DACSAuthnzDomainController", "state": "FULLY_OPERATIONAL", "info": "DACS Adapter is enabled" } ],
    [ { "name": "DACSAuthnzDomainController", "state": "FULLY_OPERATIONAL", "info": "DACS Adapter is enabled" } ]
]
```

The number of entries matches the number of MDS projectors you are running - the two above correspond to a two-projector, feed-split deployment.

---

## Where to go next

- [Enable Tokens](Cookbook-Enable-Tokens.md) - lock down the REST / management plane alongside DACS-authenticated client access.
- [Enable SSO](Cookbook-Enable-SSO.md) - add company login on top of tokens.
- [Security: Basics](Security-Basics.md) - how client and management access control fit together.
- [Static MDS](Cookbook-Deploy-Static-MDS.md) - an example of a deployment this recipe secures.
