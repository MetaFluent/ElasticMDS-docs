# Developing with TLS

When an Elastic MDS deployment serves TLS, your application connects to it the same way as before, with one setting that says "use TLS". This page covers that setting for JMS, JDBC and browser clients, how trust and client certificates are configured, and what to do about the errors you may meet. The deployment side is in [Deployment: TLS](Deployment-TLS.md).

**Audience:** Java developers, and browser-application developers. No prior TLS configuration knowledge assumed.

---

## The short version

- Set TLS to `required` in your client. Everything else follows: the handshake, certificate and host-name checks, and TLS on every connection the session makes, including the push, refresh and pub-sub connections it is redirected to.
- If the server's certificate comes from a public certificate authority, or from an authority your JVM already trusts, that is all you need.
- If the server's certificate comes from your own authority, tell the client which certificates to trust with a trust store.
- If the server asks for a client certificate (mutual TLS), give the client a key store.

---

## TLS from JMS

JMS reads its TLS settings from system properties:

| Property | Value |
|---|---|
| `com.metafluent.jms.client.Properties.Tls` | `off` (default) or `required` |
| `com.metafluent.jms.client.Properties.TrustStore` | The certificates to trust: a PEM bundle, PKCS12 or JKS file |
| `com.metafluent.jms.client.Properties.TrustStorePassword` | The trust store's password (PKCS12 or JKS) |
| `com.metafluent.jms.client.Properties.TrustStoreType` | `PEM`, `PKCS12` or `JKS`; taken from the file name when omitted |
| `com.metafluent.jms.client.Properties.KeyStore` | A PKCS12 or JKS key store holding your client certificate, for servers that require one |
| `com.metafluent.jms.client.Properties.KeyStorePassword` | The key store's password |
| `com.metafluent.jms.client.Properties.KeyAlias` | The key store entry to present, when it holds more than one |

Pass them on the command line:

```
java -Dcom.metafluent.jms.client.Properties.Tls=required \
     -cp "bin/SimpleSubscriberApplication.jar:lib/*" \
     com.metafluent.examples.simplesub.SimpleSubscriber \
     -connect mf-session:8900 -context com.metafluent.jms_context.mds RDF.VOD.L
```

or set them in code before you create the connection. A factory's own property overrides replace the system properties, which suits an application that holds several factories with different settings:

```java
import java.util.Properties;
import com.metafluent.jms.client.JavaxTopicConnectionFactory;

// Application-wide, as system properties
System.setProperty("com.metafluent.jms.client.Properties.Tls", "required");
System.setProperty("com.metafluent.jms.client.Properties.TrustStore", "/etc/myapp/ca.pem");

JavaxTopicConnectionFactory factory = new JavaxTopicConnectionFactory("mf-session:8900");

// Or per factory: these replace the system properties for this factory
Properties overrides = new Properties();
overrides.setProperty("com.metafluent.jms.client.Properties.Tls", "required");
overrides.setProperty("com.metafluent.jms.client.Properties.TrustStore", "/etc/myapp/ca.pem");
factory.setPropertyOverrides(overrides);
```

Trust and key store settings go together with `Tls=required`; giving them without it is reported as an error, so a mistyped mode never leaves TLS switched off unnoticed.

---

## TLS from JDBC

The JDBC driver takes the same settings as connection properties, with the prefix `com.metafluent.jdbc.`, or as URL parameters without the prefix:

| Connection property | URL parameter | Value |
|---|---|---|
| `com.metafluent.jdbc.tls` | `tls` | `off` (default) or `required` |
| `com.metafluent.jdbc.trust-store` | `trust-store` | PEM bundle, PKCS12 or JKS file to trust |
| `com.metafluent.jdbc.trust-store-password` | `trust-store-password` | Trust store password |
| `com.metafluent.jdbc.trust-store-type` | `trust-store-type` | `PEM`, `PKCS12` or `JKS` |
| `com.metafluent.jdbc.key-store` | `key-store` | Client certificate store, for servers that require one |
| `com.metafluent.jdbc.key-store-password` | `key-store-password` | Key store password |
| `com.metafluent.jdbc.key-alias` | `key-alias` | Key store entry to present |

The shortest form is a URL parameter:

```
jdbc:metafluent://mf-session:8900?tls=required
```

Or in code, with a trust store for your own authority and a client certificate:

```java
Properties props = new Properties();
props.setProperty("com.metafluent.jdbc.user", "guest");
props.setProperty("com.metafluent.jdbc.tls", "required");
props.setProperty("com.metafluent.jdbc.trust-store", "/etc/myapp/ca.pem");
props.setProperty("com.metafluent.jdbc.key-store", "/etc/myapp/client.p12");
props.setProperty("com.metafluent.jdbc.key-store-password", System.getenv("CLIENT_P12_PASSWORD"));

try (Connection conn = DriverManager.getConnection("jdbc:metafluent://mf-session:8900", props)) {
    // query as usual
}
```

When a setting appears both as a URL parameter and as a connection property, the URL parameter wins.

---

## The browser JavaScript client over wss://

A browser client connects to a server's WebSocket listener with a `wss://` address in place of `ws://`:

```
wss://mds.example.com:8750
```

The browser checks the server's certificate against its own trust store, so a certificate from a public CA works as it stands. For an internal authority, install that authority's certificate in the browser or the operating system's trust store, as for any other internal HTTPS site. The certificate must name the host in the address, and a page served over HTTPS connects to `wss://` addresses.

---

## Trust and client-certificate setup

**Trust.** The client verifies the server's certificate chain and its host name on every TLS connection.

- With no trust settings, the JVM's default trust applies: its list of public certificate authorities, or whatever `javax.net.ssl.trustStore` names. A server certificate from a public CA needs no client configuration.
- With a trust store setting, the certificates in that file are the ones trusted. Give your own authority's certificate (a PEM bundle is the simplest form).

**Client certificate.** When the deployment runs mutual TLS, the server asks the client to prove its identity. Give the client a key store holding its certificate and private key (PKCS12 or JKS) with the `KeyStore` and `KeyStorePassword` settings above. The client presents it when the server asks, and your operator issues it from the authority the server trusts.

---

## Errors and what to do

TLS failures are reported with the host and port, in the form `TLS handshake with <host:port> failed: <reason>`.

| What you see | What it means | What to do |
|---|---|---|
| The reason mentions a certificate path that cannot be built or validated, or an unknown authority | **Untrusted server certificate.** The server's certificate was issued by an authority the client does not trust. | Add the issuing authority's certificate to the client's trust store (`TrustStore`), or to the JVM's default trust. |
| The reason says no certificate name matches the host | **Host-name mismatch.** The certificate does not name the host the client connected to. | Connect with a host name the certificate carries, or ask your operator for a certificate that names it (see [Deployment: TLS](Deployment-TLS.md)). If you were redirected to another server, the name is the one that server advertises. |
| The TLS handshake with the server the session was redirected to fails | **A redirect to a plaintext endpoint.** A client that requires TLS performs the handshake on every connection it makes, so an endpoint that serves only plaintext cannot complete it, and no data is sent without encryption. | Ask your operator to serve TLS on the listener the redirect named (mode `offered` or `required`; see [Architecture: TLS](Architecture-TLS.md)). |
| A connect that waits about ten seconds, then says the peer accepted the connection but did not complete the handshake | **TLS requested of a plaintext listener.** The client began a handshake and the server is not speaking TLS on that port. | Connect to the port's TLS listener, or ask your operator to set the listener to `offered` or `required`. Check you used the right port for `ws://` and `wss://`. |
| The connection is closed during the handshake, or the server reports a failed certificate | **Client certificate missing or not trusted.** The server requires a client certificate and the client presented none, or one the server's authority did not issue. | Set the client's `KeyStore` (and `KeyStorePassword`) to a certificate issued by the authority your operator names. |
| An error that the connection specification asks for TLS but the client's TLS setting is off | **Conflicting settings.** A `wss://` address was given with TLS explicitly set to `off`. | Use `ws://` for plaintext, or remove the `off` setting. |
| An error that trust or key store settings are given but TLS is not `required` | **A store without the mode.** Trust or key store settings were given without `required`. | Set `Tls=required` (or `tls=required`). |

---

## Where to go next

- [Architecture: TLS](Architecture-TLS.md) - the listener modes and how clients are directed to TLS endpoints.
- [Deployment: TLS](Deployment-TLS.md) - how your operator turns TLS on, and migrates clients with offered mode.
- [JMS Application Development](Develop-JMS.md) - the JMS guide.
- [JDBC Application Development](Develop-JDBC.md) - the JDBC guide.
- [Configuration: TLS](Configuration-TLS.md) - the server-side settings.
