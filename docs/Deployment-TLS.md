# Deployment: TLS

This page takes you from a plaintext deployment to a TLS one: where the certificate files go, how to mount them in Docker Compose and Kubernetes, what a certificate has to name, how renewals are picked up without a restart, and a step-by-step migration that keeps existing clients working. Install first and refine later: the profiles and settings themselves are described in [Configuration: TLS](Configuration-TLS.md), and the model behind them in [Architecture: TLS](Architecture-TLS.md).

**Audience:** Operator, Architect.

---

## Where the files go

Every MetaFluent node looks for its TLS files in one directory:

```
/app/config/deployment-config/resources/tls/
```

Put two kinds of file there:

- **`profiles.json`** - the descriptor that defines your TLS profiles (see [Configuration: TLS](Configuration-TLS.md)).
- **The certificate, key and trust files** that `profiles.json` names.

With no `profiles.json` in the directory, the node runs without TLS, which is the default. A deployment's `deployment-config/resources/tls/` carries a `profiles.json.txt` sample; the `.txt` ending keeps the sample from being loaded. Provide your real descriptor as `profiles.json` and the files it names, with paths under `/app/config/deployment-config/resources/tls/`.

To keep the descriptor somewhere else, set `METAFLUENT_TLS_PROFILES_DESCRIPTOR` to its path, or set `tlsProfileRegistry.descriptorPath`.

---

## Mount the directory read-only

Supply the directory to each node as a read-only mount. Keys then stay in your secret store or on the host, and the same image runs everywhere.

Keep private keys and passwords out of the `deployment-config/` you bake into an image. Baking a configuration image copies everything under `deployment-config/` into the image, and a deployment project's directory is often committed to version control. A mount keeps the key material outside both.

### Docker Compose

Create a `tls` directory next to your `docker-compose.yml`, holding `profiles.json` and its files, and bind-mount it into each MetaFluent service:

```yaml
services:

  mf-session:
    image: ghcr.io/metafluent-dist-nn/mf-session-cfg-stable:milestone
    container_name: mf-session
    environment:
      METAFLUENT_HOST_UID: "${METAFLUENT_HOST_UID}"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./tls:/app/config/deployment-config/resources/tls:ro
```

Add the same `./tls:/app/config/deployment-config/resources/tls:ro` line to every MetaFluent service in the file. Docker Compose suits a demo or a lab; for production use the conventional or Kubernetes install.

### Kubernetes

Store the TLS material in a Secret and mount it as a volume. This Secret holds the descriptor and a certificate, key and CA bundle for one profile, named `internal`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mf-tls
type: Opaque
stringData:
  profiles.json: |
    [
      {
        "Name": "internal",
        "Certificate": "/app/config/deployment-config/resources/tls/tls.crt",
        "PrivateKey": "/app/config/deployment-config/resources/tls/tls.key",
        "TrustStore": "/app/config/deployment-config/resources/tls/ca.crt",
        "ClientAuth": "off"
      }
    ]
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    ...your certificate chain, server certificate first...
    -----END CERTIFICATE-----
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    ...your unencrypted PKCS#8 private key...
    -----END PRIVATE KEY-----
  ca.crt: |
    -----BEGIN CERTIFICATE-----
    ...your certificate authority...
    -----END CERTIFICATE-----
```

Mount the Secret into each MetaFluent Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: mf-session }
spec:
  replicas: 1
  selector: { matchLabels: { app: mf-session } }
  template:
    metadata: { labels: { app: mf-session } }
    spec:
      containers:
        - name: mf-session
          image: ghcr.io/metafluent-dist-nn/mf-session-cfg-stable:milestone
          volumeMounts:
            - name: tls
              mountPath: /app/config/deployment-config/resources/tls
              readOnly: true
      volumes:
        - name: tls
          secret:
            secretName: mf-tls
```

A `kubernetes.io/tls` Secret from cert-manager works the same way: its `tls.crt`, `tls.key` and `ca.crt` entries are PEM files a profile can name directly. When the Secret carries the certificate files and `profiles.json` comes from a ConfigMap or a second Secret, use a projected volume to place both in the one directory.

---

## What a certificate has to name

Clients check that the certificate names the host they connected to. For each listener, the certificate must name **the host clients use to reach it on that network**:

- the network's `AdvertiseHost`, when the network defines one, or
- the address the listener is bound to, when it does not.

Within a Docker Compose or Kubernetes deployment that is typically the service name, such as `mf-session`. For clients outside, it is the external name you advertise. See [Deployment: Advanced](Deployment-Advanced.md) for `AdvertiseHost`. A certificate can carry several names, so one certificate can serve a service name and an external name together.

Two cases carry one agreed name:

- **The fabric mesh.** Peers reach each other by IP address, so every fabric node's mesh certificate carries one shared name, such as `fabric.internal`, set as `server.tlsPeerName` (see [Configuration: TLS](Configuration-TLS.md)).
- **The gateway.** The people door's certificate names the host clients use for the gateway (the value of `METAFLUENT_API_GATEWAY_HOST`, or `mf-api-gateway` by convention). Nodes verify that name on their internal calls too.

---

## Renewing certificates without a restart

Replace the files, and the node picks them up.

- **Checked every 60 seconds by default.** Each profile compares the content of its certificate, key, trust and password files with what it last loaded. Set the interval with `tlsProfileRegistry.reloadIntervalSeconds`, or with the environment variable `METAFLUENT_TLS_RELOAD_INTERVAL_SECONDS`. A value of 0 turns checking off.
- **Renewed files are used for new connections** once they pass the same checks made at start: the files are readable, the key belongs to the certificate, and any password is right. The log records the certificate now in use (subject, serial number and expiry), as it does at start.
- **Files that fail the checks are reported** as a warning in the log, and the previous certificate stays in use. A certificate renewed a moment before its key, or a file still being written, therefore causes no interruption. Once the files are complete, the next check loads them.
- **Established connections continue.** They keep the certificate they were set up with; new connections get the renewed one.

This works with Kubernetes Secret updates, which swap the mounted files in place.

A change to `profiles.json` itself - adding, removing or renaming a profile, changing file paths or settings, or changing which profile a listener names - takes effect when the node next starts.

---

## Migrating from plaintext, step by step

Offered mode lets a listener serve plaintext and TLS clients on the same port, so you move to TLS one client at a time with no cutover moment. The migration has four steps.

**1. Add the profiles.** Create `profiles.json` and its certificate files, and mount the directory (see above). Restart the nodes. The profiles are loaded and checked, and every listener still runs as before because none names a profile yet.

**2. Set the listeners to offered.** On each client-facing server, name a profile and set the mode to `offered`:

```properties
com.metafluent.blueprint.rtc.session.server.tcpip.tcpipServer.tls=offered:public
com.metafluent.blueprint.rtc.session.server.tcpip.webSocketServer.tls=offered:public
```

These lines go in the component's file under `deployment-config/settings/` (see [Configuration: Basics](Configuration-Basics.md)). Do the same for the other servers you run (refresh, SQL, pub-sub, push, and the mesh's `tcpipServer.tls` on the data fabric). Existing plaintext clients continue to connect. TLS clients can already connect to the same ports.

**3. Move clients to TLS.** Switch each application over when convenient: JMS with `com.metafluent.jms.client.Properties.Tls=required`, JDBC with `?tls=required`, browsers with `wss://` (see [Developing with TLS](Develop-TLS.md)). Switch the node-side connections the same way: `childResultReaderFactory.tls`, `entitlementsContextConnection.tls`, `pubsubContent.tls`, and `server.outboundTls` for the mesh. A client that requires TLS is directed to endpoints that serve TLS, so redirects work throughout.

**4. Set the listeners to required.** When every client uses TLS, change `offered:public` to `required:public`. Plaintext connections are no longer accepted, and the listeners advertise `tls=on`.

The gateway's doors and the node's internal HTTP calls move as one group, because each door serves either HTTP or HTTPS on its port. When you are ready, set `restServer.tls`, `restServer.machineTls` and `internalHttp.tls` to `required:<profile>` on the gateway and the other nodes together, and restart. Move the SSO doorway at the same time.

---

## If a node does not start

A node checks its TLS settings and files when it starts, and a wrong setting stops it with a message that says what to fix: a profile name that does not exist, a file that cannot be found, a key that does not belong to its certificate, a listener that names a network it does not bind, or gateway doors that disagree. [Configuration: TLS](Configuration-TLS.md) lists the messages. Fix the setting or the file and start the node again.

---

## Where to go next

- [Configuration: TLS](Configuration-TLS.md) - the profile fields, every setting, and worked examples.
- [Architecture: TLS](Architecture-TLS.md) - the modes and how clients find TLS endpoints.
- [Developing with TLS](Develop-TLS.md) - moving applications to TLS.
- [Deployment: Advanced](Deployment-Advanced.md) - networks and `AdvertiseHost`.
- [Deployment: Basics](Deployment-Basics.md) - deployment projects and running a composition.
