# API Token Administration

**Audience:** Operators.

**How to read:** Sections 1 and 2 explain what API tokens are and how the gateway decides access. The remaining sections are tasks, in the order an operator meets them: arming a fresh gateway and minting the first administrative token, issuing tokens, listing and auditing them, and revoking or rotating them. Conceptual background — the access model and scopes — is in [Security: Basics](Security-Basics.md); single sign-on and the token internals are in [Security: Advanced](Security-Advanced.md).

Examples use the gateway host `mf-api-gateway:9090`; see [REST API](REST-API.md) for that host-name convention and its setup. Administrative actions that touch the deployment are run from the `deploy-mf-api-gateway` deployment.

## 1. Overview

An API token is a long secret string that a caller presents on each request to the API Gateway's REST interface. The gateway checks the token, confirms it carries enough authority for the operation, and then serves the request. Tokens govern the gateway's management and monitoring surface — the endpoints used by operators, scripts, and monitoring tools.

Token enforcement is active when a token store is provisioned on the primary gateway. Arming the store is a one-time operator action (Section 3). Where no token store is provisioned, the gateway serves its REST interface without requiring a token.

Two properties of the model matter in practice:

- **A token's plaintext is shown once**, when it is minted. The store keeps only a one-way fingerprint of it. A token that is lost cannot be read back — mint a replacement and revoke the old one.
- **Access is personal.** Each token is issued to a named owner and tracked on its own, so activity and revocation are per-person, not per-role.

## 2. How access is decided

Each request carries its token in the standard HTTP header:

```
Authorization: Bearer mft_aB7xQ9kJ3pZ8eR2nT5vL1qY4sW6mD0fH9gC2bV7uX
```

A MetaFluent token is recognizable by its `mft_` prefix.

The gateway grants a request when the token holds a **scope** that covers it. A scope has the form `<api>:<action>`:

- **action** is `read` for a retrieval (HTTP GET) and `write` for a change (POST, PATCH, DELETE).
- **api** names the endpoint the scope applies to, or `*` for all endpoints.

Three patterns cover most use:

| Scope | Grants |
|---|---|
| `*:read` | read-only access to all endpoints |
| `*:*` | full access to all endpoints (administrative) |
| `push:read`, `logging:write` | access to a single named endpoint (fine-grained) |

A request that carries no token, an unknown token, or a token without a covering scope is refused — `401` when the token is missing or invalid, `403` when it is valid but lacks the scope. Deny-scopes and the delegation rule are covered in [Security: Basics](Security-Basics.md).

## 3. Arming a fresh gateway: the first administrative token

A newly provisioned token store holds no tokens, so there is nothing yet to authenticate with. A one-time **bootstrap secret** covers this case: a transient credential that carries full (`*:*`) authority until the first durable token is minted.

From the `deploy-mf-api-gateway` deployment, run the generator against the primary's data directory — the host path mounted to `/app/data` in the container:

```bash
cd deploy-mf-api-gateway
scripts/generate-bootstrap-secret --data-dir /path/to/gateway/data
```

The script writes the secret to `<data-dir>/security/tokens/bootstrap.secret`, where the store reads it at startup, and prints it once to your terminal. It refuses to run if a token store or an armed secret already exists, so it cannot overwrite a live deployment.

Present the printed secret as a bearer token and mint a durable administrative token:

```bash
BOOTSTRAP="<the secret printed by generate-bootstrap-secret>"

curl -s -X POST -H "Authorization: Bearer ${BOOTSTRAP}" \
     http://mf-api-gateway:9090/api/api-tokens/v1/tokens \
     -d name=ops-admin -d ownerEmail=sam@example.com -d 'allow=*:*'
```

The response contains the new token's record and its plaintext `tokenString`. Record `tokenString` now — it is shown only here. The first successful mint retires the bootstrap secret automatically; it is no longer accepted, and the store deletes it.

From here, administer tokens with the administrative token you just minted. If every administrative token is later lost, remove the store's tokens and re-run the generator; this requires host access to the deployment — the same trust boundary as the cluster itself.

A site that manages its own secrets can skip the generator and drop its own secret at the same path, from its vault.

## 4. Issuing a token

Mint a token with a POST to the `tokens` collection.

| Parameter | Required | Meaning |
|---|---|---|
| `name` | yes | Human-readable label for the token |
| `ownerEmail` | yes | The person the token is issued to (audit attribution) |
| `allow` | yes | Comma-separated allow-scopes, e.g. `*:read` or `push:read,logging:write` |
| `deny` | no | Comma-separated deny-scopes; a deny overrides a matching allow |
| `description` | no | Free-text note |
| `expiresInDays` | no | Days until expiry. Omit for the site default (90 days); `0` for no expiry |

A read-only token for a monitoring script, set never to expire:

```bash
curl -s -X POST -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     http://mf-api-gateway:9090/api/api-tokens/v1/tokens \
     -d name=grafana -d ownerEmail=monitoring@example.com -d 'allow=*:read' -d expiresInDays=0
```

A fine-grained token limited to one endpoint:

```bash
curl -s -X POST -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     http://mf-api-gateway:9090/api/api-tokens/v1/tokens \
     -d name=push-tuning -d ownerEmail=sam@example.com -d 'allow=push:read,push:write'
```

The response is the token's record plus the plaintext `tokenString`:

```json
{
  "tokenID": "3f2a7c10-9b21-4e88-8b0c-2d5f7a1e9c34",
  "name": "grafana",
  "ownerEmail": "monitoring@example.com",
  "allow": "*:read",
  "createdAt": "2026-07-27T14:03:00Z",
  "expiresAt": null,
  "active": true,
  "tokenString": "mft_aB7xQ9kJ3pZ8eR2nT5vL1qY4sW6mD0fH9gC2bV7uX"
}
```

Capture `tokenString` and hand it to its owner through your usual secret-distribution mechanism. The gateway plays no part in how a token is transported.

**A token can only grant what its minter holds.** An administrative (`*:*`) token can mint any scope; a token holding `push:*` can mint `push:read` or `push:write`, but not `orchestration:read` or `*:read`. The full delegation rule is in [Security: Basics](Security-Basics.md).

## 5. Listing and auditing tokens

List all tokens:

```bash
curl -s -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     http://mf-api-gateway:9090/api/api-tokens/v1/tokens/*
```

The listing contains each token's record — id, name, owner, scopes, timestamps, and active state — but never a token's plaintext, which exists only in the mint response.

Filter by owner, or by active state, with the gateway's predicate grammar:

```bash
# tokens issued to one person
curl -s -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     http://mf-api-gateway:9090/api/api-tokens/v1/tokens/ownerEmail=sam@example.com/

# only active (non-revoked, non-expired) tokens
curl -s -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     http://mf-api-gateway:9090/api/api-tokens/v1/tokens/active=true/
```

Retrieve one token's record by id, projecting just the fields you want:

```bash
curl -s -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     http://mf-api-gateway:9090/api/api-tokens/v1/tokens/3f2a7c10-9b21-4e88-8b0c-2d5f7a1e9c34/name,ownerEmail,active,expiresAt
```

Each token records the id of the token that minted it (`createdBy`), giving an audit chain from any token back to the bootstrap.

## 6. Revoking and rotating a token

Revoke a token by id, with an optional audit reason:

```bash
curl -s -X DELETE -H "Authorization: Bearer ${ADMIN_TOKEN}" \
     "http://mf-api-gateway:9090/api/api-tokens/v1/tokens/3f2a7c10-9b21-4e88-8b0c-2d5f7a1e9c34?reason=owner%20left%20the%20team"
```

Revocation is a soft-delete: the record stays listable (now `active=false`, with the reason and revocation time recorded) so the audit history is kept. A revoked token stops working within the gateway's validation-cache interval (60 seconds by default) — a gateway may honor a just-revoked token until its cached copy expires.

Revoking a token does not revoke the tokens it minted. To retire a token and everything it issued, use the `createdBy` chain from Section 5 to find them and revoke each.

**Rotation** is mint-then-revoke: mint the successor, distribute it, confirm the owner has switched, then revoke the predecessor. Overlap the two so the owner is never without a working token.

## 7. Personal tokens via single sign-on

The tokens above are issued by an operator. For people working through the Dashboard, a personal token is obtained by logging in with the company single sign-on account: the Dashboard acquires a short-lived personal token on the user's behalf and uses it for that session. This path needs no operator mint and issues no long-lived secret. The single sign-on integration and the personal-token model are described in [Security: Advanced](Security-Advanced.md).
