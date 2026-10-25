# Deployment: Without Docker

Elastic MDS is designed to run as container images, but this is not required. For this purpose each deployment is released as an **installation package**: an extracted image with a host launcher script, ready to download, configure, and run.

**Audience:** operators who run software natively rather than in containers. It assumes you have read [Deployment: Basics](Deployment-Basics.md) - the deployment model, configuration, and the gateway DNS setup all apply here unchanged.

---

## Why this works

A container image is a filesystem plus a startup script and the environment it expects. Docker is one way to run that - a convenient one - but nothing about the software requires it. The installation package is that filesystem, extracted at build time, with a launcher that supplies the environment. You download it, supply your configuration, and run the launcher; there is no Docker daemon involved.

---

## What you download

Each deployment publishes its installation package as a release asset on its `deploy-mf-*` repository (for example, `deploy-mf-session`) in your `MetaFluent-Dist-NN` GitHub organization. Download the release zip and unpack it:

```
<install-dir>/
  run                              the host launcher
  app/                             the extracted image
    config/deployment-config/      your configuration: deployment.properties, settings/, resources/
    logs/                          log output and the configuration reports
```

The layout under `app/` is the same as inside the container image, so configuration and logs are where a container operator would expect them: `app/config/deployment-config/` and `app/logs/`. These are the two places you edit and read; the rest of `app/` is the product itself.

---

## Configure it

Configuration is identical to any other deployment: you edit `app/config/deployment-config/` before starting. `deployment.properties` and the per-component `settings/` files are exactly as described in [Configuration: Basics](Configuration-Basics.md) - the package ships the deployment's default configuration, and you change only what your environment requires.

The gateway host and port default to `mf-api-gateway:9090`. As with every deployment, add a DNS or `/etc/hosts` entry mapping `mf-api-gateway` to the host running the gateway (see [Deployment: Basics](Deployment-Basics.md)); the launcher prints a notice at startup if you have not set `METAFLUENT_API_GATEWAY_HOST`/`METAFLUENT_API_GATEWAY_PORT`, so the default in effect is visible.

---

## MAMA feeds

The `mf-projector-mds`, `mf-projector-mama`, and `mf-mds-consolidated` packages include the MAMA adapter, which reads OpenMAMA-bridged feeds (for example RDF/RMDS). The OpenMAMA libraries are licensed separately and supplied by you, so before the first start, put your OpenMAMA installation in place and describe your feeds:

1. **Libraries and `mama.properties`.** The package looks for them under `app/mama/`: the shared libraries (`libmama.so` and your bridge) in `app/mama/lib/`, and the directory holding `mama.properties` at `app/mama/config/`. Copy them in, or link to an existing installation:

   ```
   ln -s /opt/openmama/lib    app/mama/lib
   ln -s /opt/openmama/config app/mama/config
   ```

2. **Bridge specification.** In `app/config/deployment-config/resources/mama-adapter/`, copy `mama-spec-sample.json.txt` to `mama-spec.json` and edit it to describe your bridges and feeds.

To run a projector with ETA feeds only, turn the MAMA adapter off by setting `METAFLUENT_MAMA_DISABLED=true` in the launch environment.

---

## Run it

The launcher requires a JDK. Set `JAVA_HOME` and run `./run`:

```
export JAVA_HOME=/usr/lib/jvm/java-17
./run
```

`run` runs as the invoking account - a service user of your choosing. By default it starts the application in the **background** and returns; the process id and console output are written to `app/logs/`. Other modes:

- `./run --foreground` - stays in the foreground, which is what a service manager expects.
- `./run --enable-osgi-console` - foreground, with the interactive OSGi console.

If `JAVA_HOME` is not set, `run` stops with a clear error rather than guessing. `app/logs/` must be writable by the account you run as.

---

## Packaging for a managed install

Once you have configured and tested a setup for your environment, you can package the way you normally would:

- **RPM** (or `.deb`) - package the unpacked tree, your configuration, and a service definition as an installable OS package. Lay it under a fixed prefix, for example `/opt/elastic-mds/<image>`.
- **`systemd` unit** - with `run --foreground`, a simple service works well: `Type=simple`, `Environment=JAVA_HOME=...`, `ExecStart=/opt/elastic-mds/<image>/run --foreground`, running as your service account. `systemctl` then manages start, stop, restart, and boot.

Either gives you a Docker-free, conventionally managed install, controlled with the same tools as everything else you run.

---

## Where to go next

- [Deployment: Basics](Deployment-Basics.md) - the deployment model, configuration, and gateway DNS that this page builds on.
- [Configuration: Basics](Configuration-Basics.md) - what the configuration you supply actually contains.
- [Deployment: Advanced](Deployment-Advanced.md) - production-grade topologies and scaling.
