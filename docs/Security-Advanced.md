# Security: Advanced

This is the deeper model behind the operational surfaces in [Security: Basics](Security-Basics.md): how personal tokens actually work, how the cluster's own parts authenticate to one another (the **machine door**), and how company single sign-on is implemented. It explains *why* the pieces are shaped the way they are; the operator-facing *how to configure them* is in [Configuration: Advanced](Configuration-Advanced.md).

**Audience:** Architect, Operator.
**Prerequisites:** [Security: Basics](Security-Basics.md)

---

## One system, three postures - by what you provision

Access control on the REST / management plane is **not** three different builds and **not** a strictness knob. Every node composes the same pieces; how strict a deployment is follows from **what it provisions**. Each posture adds a layer on top of the one below:

- **Off** - nothing provisioned. No login, no tokens; the gateway serves openly, exactly as a system with no access control. The default, for labs, demos, and trusted internal networks.
- **Tokens only** - a token store is provisioned. Every call must carry a **personal token**; there is no company login, so an admin creates each person's token and hands it out.
- **Full** - additionally, the single sign-on front-door is provisioned. People are sent to their **company login**, then make their own tokens; being an admin follows from a company-login group.

Because it is one system with layers switched on, the difference between "tokens only" and "full" is only **who mints a token and how you prove you may** - an admin hands it to you, versus you log in and make it yourself. Everything downstream - the token, how a call carries it, how the gateway checks it - is identical. The enforcement point is the **gateway node**: it is the sole external ingress, so it is the only place a check is applied.

---

## How personal tokens work

### Two kinds of personal token

Even in the full setting a person ends up with tokens two ways. Both belong to that person and are tracked as that person; they differ only in how you get one and how long it lasts.

| | Made on purpose | Made for you by the browser |
|---|---|---|
| Created | By you, deliberately, at the token page | Automatically, when you log in |
| You see it? | Yes - copied once, kept safe | No - never shown |
| Lifetime | Long-lived (until it expires or you delete it) | Short - gone when the browser session ends |
| Used for | `curl`, scripts, repeated command-line work | The dashboard |

The long-lived kind is what an operator issues and manages - see [API Token Administration](API-Token-Administration.md). The short-lived kind is a detail of single sign-on, below.

### Stored as a fingerprint, never as itself

A token is built from strong randomness and shown **once**, at creation. The system keeps only a one-way **fingerprint** of it - someone who steals the store cannot recover a working token. A short fixed marker at the front (`mft_...`) lets secret-scanners and code hosts catch a token accidentally pasted into source. Tokens travel only in the request's authorization header, never in the URL, and a rejected call reveals nothing about *why* it failed (wrong, expired, or under-scoped) - full detail goes only to the server's own logs.

### How a call is checked

Every call at the gateway's people-door is checked the same way. When nothing is provisioned the door does no check and lets every call through; when a token store is armed it asks two questions in order:

1. **Is this token real, still valid, and whose is it?** Well-formed, known, not expired, not switched off. If not: `401`, stop. If yes, the caller's identity and access level are now known.
2. **Does that access cover what is being attempted?** The gateway derives the action from the HTTP method - `GET`/`HEAD` is a *read*, everything else a *change* - and checks it against the caller's scope. Not covered: `403`, stop. Otherwise it does the work.

Two design points shape this:

- **Short-term memory, with a tunable delay.** The door remembers recent answers briefly so it need not consult the store on every call. The trade-off is that switching a token off takes effect within a small, tunable window (seconds to a minute) rather than instantly. To keep a privileged **change** from riding that window, a write **bypasses the cache** and validates against the authoritative store, while a read may be served from memory. Making switch-off instant everywhere is a planned later upgrade.
- **Two access levels to start - look and change.** This matches the viewers-versus-operators picture and needs none of the fine-grained per-resource metadata, most of which the gateway does not hold locally (it proxies much of its surface from other nodes). Finer, object-level scope is a later addition.

### Two ways to become an admin

- **In the full setting**, admin authority comes from a **company-login group** (for example, membership in `metafluent-admin`), so every admin action is provable against a named person.
- **In the tokens-only setting**, there is no company login, so authority comes from **controlling the installation**: on first start the deployment generates a **one-time bootstrap secret** and surfaces it where only someone with server access can see it (the deploy log). An admin uses it **once** to mint the first real admin token, after which the bootstrap secret is retired. From then on that admin token issues everyone else's.

An admin can only ever grant access they themselves hold, and no token can be made stronger than its maker.

---

## The machine door - the system talking to itself

The cluster's parts chatter constantly with no person involved: a part starts and registers ("I'm here, and here's what I'm running"), each periodically reports "still alive" (keepalive), and the gateway gathers pieces of a picture from peers. These carry **no user token** - the cluster's parts are not people and cannot log in or fetch a personal token. Locking the people-door must not strangle that internal traffic.

**The answer is two separate doors:**

- The **people-door** - locked with login and personal tokens, on the public-facing port.
- The **machine door** - used only by the cluster's own parts, on its **own separate listener** (which a deployment binds to the private network as a hardening step; by default it listens on all interfaces), locked a different way: each part carries a shared **cluster credential** that people never hold.

The separation is the point. A stolen *people* token cannot reach cluster-internal coordination - wrong door, no credential. The cluster keeps coordinating even if the login/token system is unhealthy, because internal traffic does not depend on it. And the split is physical and provable to an auditor. The credential alone keeps a stolen people-token out even where the two doors share an interface - it carries no cluster credential; binding the machine door to the private network, a deployment hardening step, additionally puts it out of reach.

**How strong the machine door's lock is** follows the same provision-what-you-need idea:

- a **cluster-shared secret** - every part holds the same value and presents it on the machine door, which verifies it. Light, and fine for smaller sites. This is the [cluster machine secret you provision](Security-Basics.md#cluster-internal-access) in [Security: Basics](Security-Basics.md).
- proper **mutual certificates**, where each part proves it is genuine cryptographically - the enterprise default. The cluster can generate its own certificates at install, or a customer can supply their own certificate authority; a bank typically insists on the latter.

A verified peer is trusted for internal coordination - there are no finer permission levels inside the machine door, matching service-mesh convention. Everything downstream of the check (looking up the right handler, proxying) is shared between the two doors; only the check differs.

**What people see:** almost nothing - this is under the hood. The only visible touch is at install, where standing up the cluster also provisions the shared credential so the parts recognize each other.

---

## Single sign-on (full setting)

In the full setting, people authenticate with their **company login** - there are no MetaFluent-specific usernames or passwords. This is handled by a separate **login doorway**, deliberately kept out of the dashboard's request path: the dashboard is its own application, on its own origin, and it calls the gateway **directly** with a bearer token. Isolating all the company-login machinery in one front piece keeps the gateway a clean token-only API and lets the whole login layer be switched off for the tokens-only and off settings.

### The company-login contract (SAML)

The doorway speaks **SAML** to the customer's identity provider, reproducing the behaviour of the legacy MetaFluent console so an already-registered identity provider keeps working:

- The service-provider identifier (**entityID**) is `MetaFluentJMS` by default - an identifier, not an endpoint, so it stays stable when the service moves host or port and an existing registration keeps matching. It is configurable, but the default is kept for continuity.
- The identity provider's assertion is **signed and verified** against its certificate, supplied per deployment.
- A person's role is delivered as a SAML attribute, `metafluent-admin` or `metafluent-guest`, which the doorway maps to an access level - admin to full (`*:*`), guest to look-only (`*:read`).
- Logout is **local** (the doorway drops its own session); identity-provider single logout is not used, matching the legacy console.

### Login, token, and silent refresh

The doorway runs the login and then hands the dashboard **two tokens, held in the browser's memory only** - never in a cookie, never on disk, so closing the tab ends the session:

1. The dashboard, with no token yet, is sent to the doorway (a top-level navigation).
2. The doorway runs the company login and, on success, redirects back to the dashboard with a one-time code.
3. The dashboard exchanges that code for a **short-lived access token** (on the order of minutes) and a **rotating refresh token**.
4. The dashboard attaches the access token as `Authorization: Bearer` on every gateway call, direct.
5. Shortly before the access token expires, the dashboard **refreshes silently** in the background - no reload, no re-login. Each refresh rotates the refresh token, bounding the damage from a leaked one.
6. If a refresh fails or the person logs out, a single top-level redirect through the doorway restores the session - and it is silent as long as the doorway's own session is still valid.

Keeping the browser-held credential short-lived means an accidental leak has a minutes-long blast radius rather than hours; the rotation and revoke-on-logout complexity all lives server-side in the doorway, not in the dashboard.

### How the gateway trusts an access token

The single sign-on access token is **not a separate token system** - it plugs into the same validation seam a personal token uses, so the gateway still only ever sees a bearer token to check. It is a standard signed token form, signed by the doorway and **verified offline** by the gateway against the doorway's public signing certificate - no runtime call back to the doorway. The signature algorithm is pinned, which removes the classic hand-rolled-token pitfalls. Access tokens are short-lived and not individually revoked; revocation lives at the refresh layer in the doorway.

### Browsing an API URL in a browser

Pasting an API URL into a browser to see a raw result works at the **two ends** of the range, and not in the middle:

- **Off** - nothing is checked, so a raw gateway URL just works.
- **Full** - the URL is a **doorway** URL; the doorway serves it using the browser's own first-party session (running the company login first if needed), fetches the result from the gateway server-side with a bearer token, and returns it. The gateway still only ever sees a bearer, and the dashboard's direct path is untouched.
- **Tokens only** - there is no doorway to bridge it, and the gateway is bearer-only, so a raw browser navigation is refused. Browser viewing there needs a tool that sets the authorization header.

---

## Security posture - ironclad by default

In the locked settings the design follows recognized best practice, so a security-conscious customer can both choose their strictness and trust what is underneath. A site may provision less, or nothing, but that is a deliberate, owned decision - the defaults are strict:

- Tokens are stored only as a one-way fingerprint, shown once, and built from strong randomness.
- Tokens carry a scannable prefix, travel only in the authorization header, and failures reveal nothing.
- Repeated bad tokens are cheaply rejected, so they cannot overload the checker.
- **Least privilege** - everyone gets exactly the access their role grants, and no more; an admin can grant only what they hold.
- **Separate doors** - a stolen people-token cannot reach cluster internals.
- **Contained blast radius** - each cluster has its own tokens; a compromise in one does not cascade to others.
- Tokens **age out** - expiry (tunable, default 90 days, and switch-off-able) means a forgotten token does not live forever.

Every security event - a login, a token created or switched off or expired, a *denied* call - and every change operation is recorded to a **dedicated audit log**, separate from the ordinary operational logs and in a steady format a customer can collect into their own audit system. Ordinary reads are not recorded by default.

---

## Where to go next

- [Security: Basics](Security-Basics.md) - the operational surfaces this explains.
- [Configuration: Advanced](Configuration-Advanced.md) - provisioning tokens and single sign-on.
- [API Token Administration](API-Token-Administration.md) - the operator task flow for issuing and managing tokens.
- [Access Control](Access-Control.md) - the client (market-data) side of access control, a separate world from this REST/management plane.
