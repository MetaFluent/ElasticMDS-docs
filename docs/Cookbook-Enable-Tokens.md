# Cookbook: Enable Tokens

Turn on personal-token enforcement for the REST / management plane - the **tokens-only** posture, where every management call must carry a personal token. This is the ordered task; the concepts are in [Security: Advanced](Security-Advanced.md) and the configuration mechanism (and exact property names) in [Configuration: Advanced - Tokens](Configuration-Advanced.md#tokens).

**Audience:** Operator.
**Prerequisites:** a running deployment, and access to the gateway service definition and its deploy log.

---

## Before you start

- This gates the **management** plane only. Client (market-data) access is governed separately and is unaffected - see [Access Control](Access-Control.md).
- Enforcement is **presence-based**: it comes on because you provision a token store on the **primary** gateway, not from a strictness switch. Off is the default; this recipe moves you to tokens-only.

---

## Steps

1. **Give the primary gateway a persistent volume.** Mount `/app/data` on the primary gateway service (the store lives here). Only the primary needs it - secondary gateways forward token checks and stay stateless. *(→ [Configuration: Advanced - Tokens](Configuration-Advanced.md#tokens))*
2. **Provision the token store** on the primary gateway service, then restart it (no rebake) - or bake it into a `-cfg-<tag>` image to pin it. Provisioning the store **without** the `/app/data` mount is a loud startup error, not a silent half-state. *(→ [Configuration: Advanced - Tokens](Configuration-Advanced.md#tokens))*
3. **Read the one-time bootstrap secret.** On the first start with an empty volume, the gateway prints it **once** to the deploy log (`/app/logs`). Capture it now. *(→ [API Token Administration - Arming a fresh gateway](API-Token-Administration.md#3-arming-a-fresh-gateway-the-first-administrative-token))*
4. **Mint the first admin token** using that bootstrap secret. It is retired the moment the first administrative token exists. *(→ [API Token Administration - Arming a fresh gateway](API-Token-Administration.md#3-arming-a-fresh-gateway-the-first-administrative-token))*
5. **Issue per-person tokens** from the admin token - one per person or automation. *(→ [API Token Administration - Issuing a token](API-Token-Administration.md#4-issuing-a-token))*

---

## Verify

Confirm enforcement is live before you rely on it:

```bash
# No token -> refused (401)
curl -s -o /dev/null -w '%{http_code}\n' \
  "http://mf-api-gateway:9090/api/application-state/v1/*/name,state"

# With a valid token -> served (200)
curl -s -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer mft_..." \
  "http://mf-api-gateway:9090/api/application-state/v1/*/name,state"
```

The configuration self-report should also show the primary gateway with token enforcement armed (see [Configuration: Basics](Configuration-Basics.md)).

---

## Turn it off, or reset

- **Off:** remove the store provisioning and the `/app/data` mount from the gateway service and restart. With nothing provisioned the gateway serves openly again - identical to a deployment with no access control.
- **Reset:** wiping the `/app/data` volume makes the next start a fresh first boot - a new bootstrap secret is generated and the store starts empty.

---

## Related pages

- [Configuration: Advanced - Tokens](Configuration-Advanced.md#tokens) - the store, the `/app/data` mount, expiry and switch-off-delay tunables, and the exact property names.
- [API Token Administration](API-Token-Administration.md) - issuing, listing, auditing, revoking, and rotating tokens.
- [Security: Advanced](Security-Advanced.md) - how personal tokens work.
- [Cookbook: Enable SSO](Cookbook-Enable-SSO.md) - the next step, if people should log in with a company account.
