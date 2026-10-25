# Configuration: TLS

This page is the reference for TLS configuration: the profiles file, every setting that uses a profile, and worked examples for the common deployments. All settings default to off, so a deployment that sets none of them runs without TLS. Start with the examples at the end if you want a working result first, and return here for the detail.

**Audience:** Operator, Architect.

---

## TLS profiles

A profile is defined in `profiles.json`, a JSON array in `/app/config/deployment-config/resources/tls/` (see [Deployment: TLS](Deployment-TLS.md)). Each entry is one profile, and listeners and connections refer to it by `Name`.

| Field | Meaning |
|---|---|
| `Name` | How settings refer to the profile. Unique within the file. |
| `KeyStore`, `KeyStoreType`, `KeyAlias` | A keystore holding the certificate chain and private key: PKCS12 (the default) or JKS. `KeyAlias` chooses the entry when the keystore holds more than one private key. |
| `Certificate`, `PrivateKey` | The PEM alternative to a keystore: a certificate chain (server certificate first) and an unencrypted PKCS#8 private key (`BEGIN PRIVATE KEY`). This is the form cert-manager and Kubernetes TLS Secrets produce. Give a keystore or this pair, not both. |
| `TrustStore`, `TrustStoreType` | The certificates to verify peers against: a PEM bundle, a PKCS12 file or a JKS file. When omitted, the JVM's default trust applies (its list of public CAs, or `javax.net.ssl.trustStore`). |
| `KeyStorePasswordFile`, `KeyStorePasswordEnv`, `TrustStorePasswordFile`, `TrustStorePasswordEnv` | Where a store's password comes from: a file (for example a mounted Secret) or an environment variable. Passwords are kept out of the descriptor. A PEM trust bundle has no password. |
| `ClientAuth` | `off`, `optional` or `required`. Applies when a listener presents the profile: whether it asks clients for a certificate. |
| `Protocols` | Default `TLSv1.3,TLSv1.2`. |
| `CipherSuites` | Default: the JVM's enabled suites, less those excluded by current practice (the Mozilla "intermediate" list). Give a comma-separated list to choose your own. |

A profile that accepts connections needs key material. A profile used only to connect needs key material only when the listener it connects to requires a client certificate.

### Example: PEM files and a keystore

```json
[
  {
    "Name": "public",
    "Certificate": "/app/config/deployment-config/resources/tls/public/tls.crt",
    "PrivateKey": "/app/config/deployment-config/resources/tls/public/tls.key",
    "TrustStore": "/app/config/deployment-config/resources/tls/ca.crt",
    "ClientAuth": "off"
  },
  {
    "Name": "internal",
    "KeyStore": "/app/config/deployment-config/resources/tls/internal.p12",
    "KeyStorePasswordFile": "/app/config/deployment-config/resources/tls/internal.p12.password",
    "TrustStore": "/app/config/deployment-config/resources/tls/ca.crt",
    "ClientAuth": "required"
  }
]
```

The `public` profile uses PEM files and asks for no client certificate: suited to applications and browsers. The `internal` profile uses a PKCS12 keystore with its password in a file and requires client certificates: suited to node-to-node traffic.

A PKCS#1 private key (`BEGIN RSA PRIVATE KEY`) converts to PKCS#8 with `openssl pkcs8 -topk8 -nocrypt -in old.key -out tls.key`. Protect a PEM key with file permissions or a Secret; to use a password-protected key, put it in a PKCS12 keystore instead.

---

## Settings

Settings go in the component's file under `deployment-config/settings/`, using the component name as a prefix (see [Configuration: Basics](Configuration-Basics.md)). The tables show the setting as it is written inside a component; the full property name is `<component>.<setting>`.

### Values

A TLS mode setting takes `<mode>[:<profile>]`:

| Value | Meaning |
|---|---|
| `off` | Plaintext. Takes no profile. |
| `offered:<profile>` | TLS and plaintext on the same port. Available on the client-facing listeners and the mesh listener. |
| `required:<profile>` | TLS only, using the named profile. |

An outbound connection takes `off` or `required:<profile>`.

### Client-facing listeners

Components: `com.metafluent.blueprint.rtc.refresh.server.tcpip`, `...rtc.session.server.tcpip`, `...rtc.sql.server.tcpip`, `...rtc.pubsub.server.tcpip` and `...rtc.push.server.tcpip`, plus `com.metafluent.blueprint.rtc.entitlements.login.server` for the login server.

| Setting | Default | What it does |
|---|---|---|
| `tcpipServer.tls` | `off` | TLS mode of the TCP listener (JMS, JDBC and other client connections). |
| `tcpipServer.tlsNetworks` | empty | Per-network overrides for the TCP listener: a comma-separated list of `<network>=<mode>[:<profile>]`, using your network names. Empty means `tcpipServer.tls` applies on every network. |
| `webSocketServer.tls` | `off` | TLS mode of the WebSocket listener (browser clients: `wss://`). Available on the refresh, session, SQL and pub-sub servers. |
| `webSocketServer.tlsNetworks` | empty | Per-network overrides for the WebSocket listener, in the same form. |

Example - plaintext on the private network and TLS on the client network, for a TCP listener; `wss` only for browsers:

```properties
com.metafluent.blueprint.rtc.refresh.server.tcpip.tcpipServer.tls=off
com.metafluent.blueprint.rtc.refresh.server.tcpip.tcpipServer.tlsNetworks=client=required:public
com.metafluent.blueprint.rtc.refresh.server.tcpip.webSocketServer.tls=required:public
```

A network named in `tlsNetworks` must be one the listener binds; a misspelt name stops the node at start and says so.

### API gateway and SSO

| Component | Setting | Default | What it does |
|---|---|---|---|
| `com.metafluent.blueprint.core.utilities` | `restServer.tls` | `off` | The people door: `off` (HTTP) or `required:<profile>` (HTTPS). The profile's certificate names the host clients use for the gateway. API documents then give `https` addresses. |
| `com.metafluent.blueprint.core.utilities` | `restServer.machineTls` | `off` | The machine door, in the same form. The certificate names the host this node advertises for its machine door (`restServer.machineHost`). |
| `com.metafluent.blueprint.security.rest.sso` | `sso.tls` | `off` | The SSO login doorway: `off` or `required:<profile>`. The certificate names the host browsers use to reach it. With HTTPS, `sso.acsURL`, `sso.tokenIssuer` and the redirect addresses it is configured with use `https` URLs too. |

`restServer.tls`, `restServer.machineTls` and `internalHttp.tls` are all `required:<profile>` or all `off`. A node whose three settings disagree stops at start and names the settings. Their profiles may differ.

```properties
com.metafluent.blueprint.core.utilities.restServer.tls=required:public
com.metafluent.blueprint.core.utilities.restServer.machineTls=required:internal
com.metafluent.blueprint.network.registry.internalHttp.tls=required:internal
```

### Internal connections

| Component | Setting | Default | What it does |
|---|---|---|---|
| `com.metafluent.blueprint.network.registry` | `tlsProfileRegistry.descriptorPath` | `$(METAFLUENT_TLS_PROFILES_DESCRIPTOR:$(METAFLUENT_CONFIG_RESOURCES)/tls/profiles.json)` | Path to the profiles file. A file that is present must load completely, or the node does not start. |
| `com.metafluent.blueprint.network.registry` | `tlsProfileRegistry.reloadIntervalSeconds` | `$(METAFLUENT_TLS_RELOAD_INTERVAL_SECONDS:60)` | How often, in seconds, profiles check for renewed files. 0 turns checking off. |
| `com.metafluent.blueprint.network.registry` | `internalHttp.tls` | `$(METAFLUENT_INTERNAL_HTTP_TLS:off)` | How the node makes its internal HTTP calls: `off` or `required:<profile>`. With `required`, each call uses HTTPS, verifies the door's certificate and host name with the profile's trust, and presents the profile's certificate if the door asks. |
| `com.metafluent.blueprint.datafabric` | `tcpipServer.tls` | `off` | TLS mode of the fabric mesh listener (inbound), including `offered`. |
| `com.metafluent.blueprint.datafabric` | `tcpipServer.tlsNetworks` | empty | Per-network overrides for the mesh listener. |
| `com.metafluent.blueprint.datafabric` | `server.outboundTls` | `off` | TLS on this node's connections to its mesh peers: `off` or `required:<profile>`. |
| `com.metafluent.blueprint.datafabric` | `server.tlsPeerName` | empty | The name every fabric node's mesh certificate carries, for example `fabric.internal`. Peers are verified against it. Needed when `server.outboundTls` is `required`. |
| `com.metafluent.blueprint.rtc.content.common` | `childResultReaderFactory.tls` | `off` | TLS for reading other nodes' results: `off` or `required:<profile>`. Orchestration then places those reads on listeners that serve TLS. |
| `com.metafluent.blueprint.rtc.query.proxy.authnz` | `entitlementsContextConnection.tls` | `off` | TLS for the session with the entitlements server. |
| `com.metafluent.blueprint.rtc.content.adapter.mfpubsub` | `pubsubContent.tls` | `off` | TLS for the pub-sub adapter's session with the data tier and its REST calls to it (TLS and HTTPS when required). |

The `tlsProfileRegistry` settings can also be set from the environment: `METAFLUENT_TLS_PROFILES_DESCRIPTOR`, `METAFLUENT_TLS_RELOAD_INTERVAL_SECONDS` and `METAFLUENT_INTERNAL_HTTP_TLS`.

Example - reload every 5 minutes, and keep the profiles file in a custom location:

```properties
com.metafluent.blueprint.network.registry.tlsProfileRegistry.descriptorPath=/etc/metafluent/tls/profiles.json
com.metafluent.blueprint.network.registry.tlsProfileRegistry.reloadIntervalSeconds=300
```

---

## Worked examples

### wss for browser clients

Browsers connect with secure WebSockets to a server's WebSocket listener. This example serves the refresh server's browser listener over TLS, with a public certificate, and leaves its TCP listener as it is.

`profiles.json`:

```json
[
  {
    "Name": "public",
    "Certificate": "/app/config/deployment-config/resources/tls/tls.crt",
    "PrivateKey": "/app/config/deployment-config/resources/tls/tls.key",
    "ClientAuth": "off"
  }
]
```

Setting:

```properties
com.metafluent.blueprint.rtc.refresh.server.tcpip.webSocketServer.tls=required:public
```

The certificate names the host the browser connects to, and a certificate from a public CA is trusted by the browser as it stands. Browsers connect to `wss://host:port`; see [Developing with TLS](Develop-TLS.md). To keep serving existing `ws://` pages during a migration, use `offered:public` instead; one port then serves `ws://` and `wss://`.

### An all-TLS deployment

Every connection uses TLS: client APIs, browsers, the mesh, internal reads and the gateway. Two profiles do the work. `public` presents the certificate to applications and browsers and asks for no client certificate. `internal` is used between nodes and requires client certificates. Both certificates are issued by the one CA in `ca.crt`, which every node trusts.

`profiles.json`:

```json
[
  {
    "Name": "public",
    "Certificate": "/app/config/deployment-config/resources/tls/public/tls.crt",
    "PrivateKey": "/app/config/deployment-config/resources/tls/public/tls.key",
    "TrustStore": "/app/config/deployment-config/resources/tls/ca.crt",
    "ClientAuth": "off"
  },
  {
    "Name": "internal",
    "Certificate": "/app/config/deployment-config/resources/tls/internal/tls.crt",
    "PrivateKey": "/app/config/deployment-config/resources/tls/internal/tls.key",
    "TrustStore": "/app/config/deployment-config/resources/tls/ca.crt",
    "ClientAuth": "required"
  }
]
```

Settings, for the client-facing servers (repeat for each server you run; the WebSocket line applies to refresh, session, SQL and pub-sub):

```properties
com.metafluent.blueprint.rtc.session.server.tcpip.tcpipServer.tls=required:public
com.metafluent.blueprint.rtc.session.server.tcpip.webSocketServer.tls=required:public
```

Settings, for the fabric mesh:

```properties
com.metafluent.blueprint.datafabric.tcpipServer.tls=required:internal
com.metafluent.blueprint.datafabric.server.outboundTls=required:internal
com.metafluent.blueprint.datafabric.server.tlsPeerName=fabric.internal
```

Settings, for internal reads and sessions between nodes:

```properties
com.metafluent.blueprint.rtc.content.common.childResultReaderFactory.tls=required:internal
com.metafluent.blueprint.rtc.query.proxy.authnz.entitlementsContextConnection.tls=required:internal
com.metafluent.blueprint.rtc.content.adapter.mfpubsub.pubsubContent.tls=required:internal
```

Settings, for the gateway and SSO (all three gateway settings agree):

```properties
com.metafluent.blueprint.core.utilities.restServer.tls=required:public
com.metafluent.blueprint.core.utilities.restServer.machineTls=required:internal
com.metafluent.blueprint.network.registry.internalHttp.tls=required:internal
com.metafluent.blueprint.security.rest.sso.sso.tls=required:public
```

Certificate names: each listener's certificate names the host its clients use; the `internal` certificate carries `fabric.internal` for the mesh. The `public` certificate on the people door must be one the nodes trust, which the shared CA in `ca.crt` provides, because every node also calls that door.

### Mutual TLS for internal connections

Keep the client-facing side as it is, and have the nodes authenticate each other with certificates. A listener on the private network requires a client certificate, and the nodes that connect to it present theirs.

Profile `internal` has `"ClientAuth": "required"` (as above). Settings, on a server whose private network is named `private`:

```properties
# the private network requires TLS with client certificates; other networks are unchanged
com.metafluent.blueprint.rtc.refresh.server.tcpip.tcpipServer.tlsNetworks=private=required:internal

# nodes reading from that listener use the same profile: trust to verify it, certificate to present
com.metafluent.blueprint.rtc.content.common.childResultReaderFactory.tls=required:internal
```

A connecting node verifies the listener against the profile's `TrustStore` and presents the profile's certificate when the listener asks for one. The same pattern covers the mesh: `tcpipServer.tls`, `server.outboundTls` and `server.tlsPeerName` on the data fabric with `required:internal`.

---

## Start-up messages

A node reads and checks every profile and TLS setting when it starts. If something is off, it stops with a message that says what to fix. The common ones:

| The message says | What to do |
|---|---|
| A profile has no `Name` | Give every profile a unique `Name`. |
| A setting names a profile that does not exist, or the node has no profiles | Add the profile to `profiles.json`, or correct the name in the setting. |
| A `required` mode needs a profile, as `required:<profile>` | Add the profile name to the setting. |
| A mode `off` takes no profile | Remove the profile name, or change the mode. |
| A file was not found | Check the path in `profiles.json` and that the directory is mounted. |
| A profile gives both a `KeyStore` and a `Certificate`/`PrivateKey`, or only one of the PEM pair | Give a keystore, or both PEM files. |
| A keystore needs a password | Set `KeyStorePasswordFile` or `KeyStorePasswordEnv`. |
| A keystore holds several private keys | Set `KeyAlias` to choose one. |
| The private key is in PKCS#1 format | Convert it with the `openssl pkcs8 -topk8 -nocrypt` command the message shows. |
| The private key is encrypted | Use an unencrypted PKCS#8 key (protected by file permissions or a Secret), or a password-protected PKCS12 keystore. |
| The private key does not belong to the certificate | Supply the matching key and certificate. |
| A `...Env` password names an environment variable that is not set | Set the variable. |
| TLS is required for the mesh without a peer name | Set `server.tlsPeerName`. |
| A listener names a network it does not bind | Correct the network name in `tlsNetworks`. |
| The gateway doors and internal HTTP disagree | Set `restServer.tls`, `restServer.machineTls` and `internalHttp.tls` all to `required:<profile>`, or all to `off`. |
| `offered` is set on an HTTP door | Use `off` or `required:<profile>`; offered mode applies to the client-facing listeners and the mesh. |

---

## Where to go next

- [Deployment: TLS](Deployment-TLS.md) - mounting the files, renewing certificates and migrating from plaintext.
- [Architecture: TLS](Architecture-TLS.md) - the modes, mutual TLS and how clients find TLS endpoints.
- [Developing with TLS](Develop-TLS.md) - the client-side settings for JMS, JDBC and browsers.
- [Configuration: Reference](Configuration-Reference.md) - the annotated properties for every setting.
- [Configuration: Advanced](Configuration-Advanced.md) - how a final value is assembled.
