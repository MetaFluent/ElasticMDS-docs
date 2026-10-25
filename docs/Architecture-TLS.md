# Architecture: TLS

Elastic MDS can encrypt and authenticate every connection it makes: the ones your applications open, the ones browsers open, and the ones the nodes open to each other. You choose, connection by connection, when to turn TLS on. This page describes what can use TLS, the three modes a listener can run in, how mutual TLS fits in, and how clients are steered to endpoints that serve TLS. The practical steps are in [Deployment: TLS](Deployment-TLS.md), the settings in [Configuration: TLS](Configuration-TLS.md), and the client side in [Developing with TLS](Develop-TLS.md).

**Audience:** Architect, Operator.

---

## The security standard

TLS in Elastic MDS follows current practice for a security-conscious client, and the same rules apply to every connection:

- **TLS or an error.** A connection that requires TLS gets TLS, or stops with an error that says why. Plaintext is never used as a fallback.
- **Peers are verified.** The certificate chain and the host name are always checked. Verification is built in to every TLS connection.
- **Current protocols.** TLS 1.3 and TLS 1.2, with current cipher suites. An older version is used only when a profile lists it explicitly.
- **Mutual TLS when you want it.** A listener can ask for client certificates, or require them.
- **Checked at start.** A wrong or missing setting stops the node when it starts, with a message saying what to fix. Every certificate, key and trust file is read and checked at that point.

TLS is off by default. A deployment with no TLS configuration behaves exactly as it always has, and you turn TLS on when you are ready.

---

## What can use TLS

| Connection | Who opens it | Covered by |
|---|---|---|
| Client APIs - JMS and JDBC | Your applications | TLS on the client-facing listeners (session, SQL, pub-sub, push, refresh) |
| Browser and JavaScript clients | Browsers | Secure WebSockets (`wss://`) on the same servers |
| Node-to-node: the fabric mesh | Each fabric node, to its peers | TLS on the mesh listener and on each node's outbound mesh connections |
| Node-to-node: internal reads | A node reading another node's results, or a node reaching the entitlements or data tier | TLS on the reading side, served by the listeners above |
| API gateway - the people door | People and applications calling the REST API | HTTPS on the people door |
| API gateway - the machine door | The nodes' own registration and coordination traffic | HTTPS on the machine door |
| Internal HTTP | Every node's calls to the gateway, and the gateway's calls to other nodes | One setting per node |
| SSO login doorway | Browsers signing in | HTTPS on the doorway |

Each row is independent. You can encrypt the client-facing servers and leave the private network as it is, or encrypt everything; [Configuration: TLS](Configuration-TLS.md) has a worked example of each.

---

## TLS profiles

A **TLS profile** is a named bundle of certificate, private key, trusted certificates and policy. You define profiles once, in a `profiles.json` file, and every listener and connection that needs TLS refers to one by name. A profile used by a listener presents that profile's certificate; a profile used by an outbound connection supplies the certificates to trust and, when the listener asks for one, the client certificate.

Profiles keep certificate handling in one place: renewing a certificate means replacing its files, and every listener that uses the profile picks up the new certificate (see [Deployment: TLS](Deployment-TLS.md)). The fields are in [Configuration: TLS](Configuration-TLS.md).

---

## Listener modes

Every client-facing listener has a TLS mode, set per listener and, where a server binds several networks, per network:

| Mode | The listener accepts | Use it for |
|---|---|---|
| **off** (the default) | Plaintext only | A deployment that does not use TLS yet, or a trusted private network |
| **offered** | Plaintext and TLS on the same port. The client's first byte decides which. | Migrating from plaintext to TLS while existing clients keep working |
| **required** | TLS only | The destination: every client uses TLS |

In **offered** mode a single port serves both kinds of client. A TLS connection begins with a handshake record and a plaintext connection begins with a protocol message, so the listener tells them apart before it reads anything else. On a WebSocket listener, offered mode serves `ws://` and `wss://` on one port. Offered mode is the bridge that lets you move clients to TLS one at a time, then close the plaintext door with **required**; the steps are in [Deployment: TLS](Deployment-TLS.md).

The HTTP listeners (the gateway's two doors and the SSO doorway) each serve either plaintext or TLS, so they take **off** or **required**.

---

## Mutual TLS

A server always proves its identity to the client. With mutual TLS the client proves its identity as well, using a certificate. Mutual TLS is a property of the profile a listener presents, through its `ClientAuth` field:

- **off** - the listener does not ask for a client certificate.
- **optional** - the listener asks for one and accepts a connection without one.
- **required** - the listener refuses a client that does not present a certificate the profile trusts.

Because it belongs to the profile, you can run different policies side by side: a `public` profile with client certificates off for applications and browsers, and an `internal` profile with client certificates required for node-to-node traffic. Nodes that connect to a listener requiring a client certificate present the certificate of their own profile automatically.

---

## How clients find TLS endpoints

Clients do not choose endpoints; the servers hand them out. A client connects to a session server, and the servers then direct it to the push, refresh or pub-sub server that holds its content. TLS fits into that hand-off:

- **Each listener advertises whether it serves TLS.** A listener in required mode advertises `tls=on`. A listener in off mode advertises `tls=off`. A listener in offered mode serves both kinds of client, so it matches either.
- **A client is sent to an endpoint of its own kind.** A session that arrived over TLS is directed only to listeners that serve TLS, and a plaintext session only to listeners that serve plaintext. A browser on `wss://` stays on `wss://`.
- **Internal reads follow the reader.** When a node reads another node's results, orchestration places the work on listeners that match the reader's TLS setting.
- **The client's own setting has the last word.** A client that requires TLS always performs the handshake and verifies the server, on every connection it makes. If it ever reaches an endpoint that serves only plaintext, the handshake fails with a clear connection error, and no data is sent without encryption.

The practical effect: turn TLS on in the client, and the whole session, redirects included, uses TLS.

---

## Gateway and SSO

The API gateway has two doors, and each can serve HTTPS:

- The **people door** is the REST API for people and applications.
- The **machine door** carries the nodes' own coordination traffic (see [Security: Advanced](Security-Advanced.md)).

Every node also makes internal HTTP calls to the gateway, and the gateway makes calls to other nodes' doors. These calls are all HTTP or all HTTPS together, so the people door, the machine door and the node's internal HTTP setting move as one: all required, or all off. A node whose settings disagree stops at start and names the settings. When a node registers, it announces the scheme of each door, so callers connect with the right one.

The SSO login doorway is HTTPS-capable in the same way.

---

## Where to go next

- [Deployment: TLS](Deployment-TLS.md) - where the files go, mounting them, rotating certificates, and migrating from plaintext.
- [Configuration: TLS](Configuration-TLS.md) - profiles, every setting, and worked examples.
- [Developing with TLS](Develop-TLS.md) - connecting from JMS, JDBC and the browser.
- [Security: Basics](Security-Basics.md) - the other security surfaces.
- [Deployment: Advanced](Deployment-Advanced.md) - networks and the addresses clients are given.
