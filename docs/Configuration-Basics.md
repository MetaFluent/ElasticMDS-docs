# Configuration: Basics

A deployment is configured the same way regardless of how you run it. [Deployment: Basics](Deployment-Basics.md) covers the three ways to run one - Docker or Kubernetes with a mounted configuration volume, a configuration baked into the image, or the downloaded installation package for a conventional install - and each reads the same `deployment-config/`. This page covers that configuration: where you set values, what the entry-point file contains, and how to confirm what a running system is using.

**Audience:** administrators and operators configuring a deployment. It assumes you have read [Deployment: Basics](Deployment-Basics.md).

---

## Where configuration lives

Whichever way you run it, a deployment is configured under `deployment-config/`:

- **`deployment.properties`** - the entry point. This is the first file you open.
- **`settings/`** - one file per component, holding that component's operator settings. You open the file for the concern you are configuring.
- **`resources/`** - files that settings refer to (for example, orchestration policies). You add or adapt these as your deployment requires.

Where `deployment-config/` sits depends on how you run the deployment: it is the volume you mount into the running service under Docker or Kubernetes, the configuration you set before "baking" a configured image, or the `deployment-config/` inside the unpacked installation package for a conventional install. In every case the files, and how you edit them, are the same - covered below.

For the most part, a deployment ships with a default for everything, so it runs without your setting much. You change only what your environment requires; the rest stays at its default. Required settings usually relate to external integrations.

Configuration takes effect when the service starts. A baked image freezes it at build time; to change a baked configuration you rebuild the configured image (see [Deployment: Basics](Deployment-Basics.md)).

---

## The entry point: deployment.properties

`deployment.properties` is kept short, so the decisions that matter are in front of you. It contains three kinds of entry and points to the per-component settings files for the rest.

**Switches.** On/off decisions for this deployment are listed first - whether DACS authentication is active, which authorization provider a content adapter uses, and the like. Set the value and start:

```
com.metafluent.blueprint.authnz.dacs.dacsAuthnz.disabled=true
```

**Required values.** Some deployments have values you must supply. They ship empty, grouped under a REQUIRED heading. Fill them in before you start.

**Settings, per component.** The adjustable settings are not listed in `deployment.properties` itself. Each component keeps its settings in its own file under `settings/`, pulled in automatically; `deployment.properties` lists which files are present:

```
#   settings/com.metafluent.blueprint.authnz.dacs.properties
#   settings/com.metafluent.blueprint.rtc.content.adapter.eta.properties
```

Open the file for the component you are configuring. Each setting carries a one-line summary and its default, ready to change:

```
# Seconds between DACS reconnect attempts.
com.metafluent.blueprint.authnz.dacs.dacsAuthnz.retryRateSeconds=2
```

The full documentation for a component's settings is in the matching `-reference.txt` beside it - for example, `settings/com.metafluent.blueprint.authnz.dacs-reference.txt`. The reference is read-only; you set values in the `.properties` file.

Some values are written as `$(NAME)` or `$(NAME:default)`. These read from an environment variable, with an optional fallback, so the same configuration can be driven by the environment it runs in - useful when one configuration is used across several hosts.

---

## There is more than what you see

The switches and the per-component settings files contain the values you are most likely to change. A running system has many more properties than appear there; each has a default. Most of the time you won't need to change any of these. To see the complete picture - each property in effect, not just the ones you changed - use the reports below.

---

## Seeing the configuration in effect

There are two ways to see exactly what a running system is configured with.

**Reports in the log directory.** At startup, each component writes its configuration to its log directory as two reports:

- a **full** report - each property in effect (file ending `-FullPropertiesReportXMLFile.xml`), and
- a **modified** report - only the properties that differ from their defaults (file ending `-ModifiedPropertiesReportXMLFile.xml`).

Each entry shows the component, the property, its default, and the value in effect. The modified report is the quick answer to "what has this deployment changed?"

**From a running system, over the gateway.** The same information is available live through the gateway's `config` API. Ask for just the non-default properties - the "what has this deployment changed?" view - across all components:

```
curl -s "http://mf-api-gateway:9090/api/config/v1/*/allModifiedProperties?bundleName=.*"
```

The response lists each component and the properties it has changed, with both the default and the value in effect:

```json
{
  "bundleName": "com.metafluent.blueprint.authnz.dacs",
  "bundleVersion": "6.8.0",
  "properties": [
    { "name": "dacsAuthnz.disabled",
      "default": "true",
      "actual": "false" }
  ]
}
```

Use `fullProperties` in place of `allModifiedProperties` for each property in effect, not just the changed ones. The exact calls, and how to turn a report into a version-accurate reference for your release, are covered in [Configuration Reference](Configuration-Reference.md).

---

## Where to go next

- [Configuration: Advanced](Configuration-Advanced.md) - the configuration a non-trivial deployment needs beyond the defaults.
- [Configuration Reference](Configuration-Reference.md) - getting the exact, version-accurate settings for your release.
- [Deployment: Basics](Deployment-Basics.md) - the three ways to run a deployment, and where its configuration lives.
- [Operations: Monitoring & Diagnostics](Operations-Monitoring.md) - querying a running system through the gateway.
- [Glossary](Glossary.md) - definitions of the terms used here.
