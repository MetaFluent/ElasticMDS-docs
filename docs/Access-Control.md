# Access Control

Access control in Elastic MDS answers two questions about every connecting application: **who is it** (authentication) and **what content may it read or change** (entitlements). The two are decided independently - a deployment chooses how clients authenticate and, separately, which access-control service entitles them - and both are **live**, re-evaluated while a client stays connected rather than settled once at login.

**Audience:** Architect.
**Prerequisites:** [Architecture: Basics](Architecture-Basics.md)

---

## Client authentication

The session server authenticates connecting applications according to its configured **authentication domain**, set per deployment through the `authenticationDomain` switch (see [Configuration: Basics](Configuration-Basics.md)):

- **None** (`NO-AUTHN`) - no authentication; any client is accepted. The default, appropriate for closed or development networks where the network itself is the boundary.
- **DACS** - clients are authenticated against a Refinitiv **DACS** daemon, the standard choice where DACS governs market-data access.

The authentication framework itself is flexible:

- **Authentication can be refreshed** - a client's authenticated status can change during the life of a connection, not only at login.
- **It is independent of authorization** - the mechanism that authenticates a client is decoupled from the one that entitles it, so the two are chosen separately.
- **It supports multiple principals (Subjects)** - a single connection can be authenticated in more than one domain at once.

Authentication establishes the connection **identity**, and that identity is what the entitlements framework evaluates access against.

---

## Entitlements (authorization)

Where authentication settles *who* is connected, **entitlements** decide *what content* an identity may access. Elastic MDS treats entitlement as a pluggable **access-control service**: the reference integration is **DACS**, and an alternative access-control system can be integrated behind the same abstraction.

Architecturally, each **content adapter** is configured to reach an entitlements service through a common **entitlements service abstraction**. Adapters are bound independently - **not every adapter has to use the same implementation** - so one deployment can govern one source through DACS and another through a different system.

The authorization framework:

1. **Read access** is controlled at the **item / row** level.
2. **Write access** is controlled at the **item / row** level.
3. Access control is **live** - a client's read or write access can be **refreshed at any time**, so entitlements can be granted or revoked while the client stays connected.

*Advanced: within some adapters the entitlements binding is finer still - per table - so different tables served by one adapter can be governed by different entitlements services.*

---

## Transitive entitlement for derived content

Elastic MDS produces **derived content** - values computed from other content, such as a mid price calculated from bid and ask, or a view that joins several tables (see [Architecture: Basics](Architecture-Basics.md)). Access control follows the computation:

> **Read access to a piece of derived content requires access to every input it is derived from - transitively.**

If a client is not entitled to one of the inputs, it is not entitled to the derived result, no matter how deep the derivation chain runs. The entitlement of a result is never weaker than the entitlement of its inputs - so a computed column or a view cannot be used to launder access to content a user is not permitted to see. Entitlement is enforced on the underlying content, not on the presentation of it.

---

## Related pages

- [Configuration: Basics](Configuration-Basics.md) - setting the client-authentication switch.
- [Entitlements Context](Entitlements-Context.md) - querying the entitlements system from an application.
- [Security: Basics](Security-Basics.md) - the operational security surfaces: REST/admin access, cluster-internal traffic, transport, and deployment secrets.
