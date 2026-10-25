# Entitlements Context

Elastic MDS exposes an entitlements service over JMS: an application can check whether an identity is permitted to access a unit of content, independently of retrieving the content itself. This is useful for applications that must enforce access control - either for themselves or on behalf of their own users.

Entitlement checks use a dedicated context, and the mechanics are more involved than the content ([MarketData](Develop-JMS.md#the-marketdata-context-explicit-generic)) context. Elastic MDS does not change the entitlements model from MetaFluent v5.

This page is the developer interface for *checking* entitlements. For the entitlements framework architecture - how DACS (or an alternative) integrates as the access-control service, and how access applies down to derived content - see [Access Control](Access-Control.md).

**Audience:** developers integrating access control.

---

## The context

Create the JMS session with the entitlements application context, `com.metafluent.jms_context.entitlements` (version-qualified, for example `com.metafluent.jms_context.entitlements-3`). Two things differ from the content context:

- **Topic names use a comma (`,`) delimiter**, not a dot.
- **Subscriptions deliver only STATUS messages** - no field data. The status carries the decision: an `OK` status means access is allowed; a `DENIED` status means it is not. The accompanying text gives an informational reason. See [Dynamic Data Conventions](Dynamic-Data-Conventions.md) for status handling.

The connection identity (user name) is the identity the entitlement is evaluated against. A connection is rejected if the identity is invalid or would exceed the allowed number of simultaneous connections.

---

## Use-cases

There are four patterns, along two axes: whether the application checks access **for itself** (self) or **on behalf of end-users** (proxy), and whether it passes an explicit **entitlement code**.

### Self-entitlement

An application that accesses access-controlled data **on its own behalf**. It has its own session with Elastic MDS, and its connection identity is the basis for the entitlement check. Before using a unit of content - whether it comes from Elastic MDS or from an external source - the application checks its own access to it.

For each symbol, subscribe to a topic naming the feed and symbol:

```
feed,symbol          e.g.  CTA,R.T
```

`OK` means the data may be used; `DENIED` means it may not. Unsubscribe when the symbol is no longer in use. (The server holds a subscription to the entitled data on your behalf; the data events themselves are discarded.)

### Proxy entitlement

An application that accesses data **on behalf of some other user identity** - for example a web application whose users log in to see their portfolios. The application (the **proxy**) obtains the data under its own identity - from an external source, or from Elastic MDS - and forwards it to the user, but the entitlement is checked against the **end-user's** identity, not the proxy's.

The proxy connects with its own valid identity, then:

1. When a user starts, subscribe to a **login** topic and keep it open (a forced log-off or a profile change arrives on it):

    ```
    login,user-id,application-id,ip-address    e.g.  login,joe,someApp,10.1.1.1
    ```

2. For each symbol the user accesses, subscribe to a **subscription** topic:

    ```
    subscription,user-id,application-id,ip-address,feed,symbol
    ```

`OK` allows the user access; `DENIED` denies it. Unsubscribe from a subscription topic when the user stops using the symbol, and from the login topic when the user is no longer active.

### Code-based variants

If the application already has an **entitlement code** for the content (a numeric value from the feed handler identifying a class of access-controlled data), it can encode that in the topic. The server then does not need to hold a subscription to the entitled data:

```
code,feed,entitlements-code[,symbol]                                          (self)
    e.g.  code,IDN_RDF,52,IBM.N

code,subscription,user-id,application-id,ip-address,feed,entitlements-code[,symbol]   (proxy)
```

---

## Design notes

- Entitlements applications do not publish.
- **Proxy state.** A login has a one-to-many relationship with its subscriptions. Track it - typically a per-login object holding the associated subscriptions. If the login is closed, drop all of its subscriptions and revoke the corresponding access.
- A `DENIED` (or `CLOSED` / `INVALID`) status can arrive **after** a subscription has succeeded - for example when an entitlement is withdrawn. Handle status changes for the life of the subscription, not only at start.
- Code-based self-entitlement usually requires reading the data first to obtain the code, which makes proving compliance harder than the plain self-entitlement pattern.

---

## Where to go next

- [JMS Application Development](Develop-JMS.md) - the JMS basics these patterns build on.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - interpreting the status messages.
