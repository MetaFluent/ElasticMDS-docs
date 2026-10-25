# Configuration Reference

This is a reference you get **from the product**, not one this guide ships. Elastic MDS carries its own configuration reference in two complementary forms, each always accurate for the exact release you run:

- the **annotated properties files** baked into each image, which explain what every setting *means*, and
- the **live self-report** over the gateway, which shows what every setting is *set to*.

[Configuration: Basics](Configuration-Basics.md) covers setting values and the on-disk reports; [Configuration: Advanced](Configuration-Advanced.md) covers how a final value is assembled. This page is those two forms of the reference and how to read them.

**Audience:** Administrator, Operator.

---

## Why there is no master list here

A printed table of "every setting and its default" would be wrong almost immediately. The complete set of settings, and their defaults, depends on the **version** you run and on which **components** your deployment includes. So rather than reproduce a table that would rot, Elastic MDS ships the reference inside the product, version-stamped, and lets the running system report itself.

---

## The annotated reference in each image

Every component (blueprint) contributes a **generated, fully commented properties file** describing all of its settings. These are baked into each image under `/app/config/defaults/`, one file per component:

```
/app/config/defaults/com.metafluent.blueprint.rtc.session.server.tcpip.properties
/app/config/defaults/com.metafluent.blueprint.rtc.push.server.tcpip.properties
/app/config/defaults/com.metafluent.blueprint.core.utilities.properties
...
```

Each file is organised by **bean** (a configurable object within the component), and for every setting gives a description and its default:

```
# Component: com.metafluent.blueprint.rtc.session.server.tcpip
# [Generated from version 6.3.0]
...
# Bean: tcpipServer
# Purpose:
#   TCP/IP network server
######################
# Property: server.default
# Description:
#   Default network port
# [Default: 8900]
#
server.default=8900
```

These files are the **"what does it mean"** reference - the descriptions live here, in the image, not in the wiki, so they always match the version you are running. Extract them with plain Docker:

```
# Copy every annotated file out of a running container:
docker cp <container>:/app/config/defaults ./config-defaults

# Read one component's file without copying it out:
docker exec <container> cat /app/config/defaults/com.metafluent.blueprint.rtc.session.server.tcpip.properties

# Or straight from an image, with nothing running:
id=$(docker create <image>); docker cp "$id":/app/config/defaults ./config-defaults; docker rm "$id"
```

Running a conventional installation package instead of Docker? The same annotated files sit under `app/config/defaults/` in the unpacked tree - just read them directly, no Docker required (see [Deployment: Without Docker](Deployment-Without-Docker.md)).

Note the version stamp in the header (`from version 6.3.0`): the file documents *exactly* the settings and defaults of the component version in that image.

---

## Short names and fully-qualified names

The annotated files use **short** property names - `manager.etaServerHost`, `server.default` - each scoped to the single component its file documents. The short form is where every setting is *defined*, and for **most settings it is the only place they appear**: the majority are never written out in fully-qualified form anywhere in a deployment.

A **fully-qualified name** prefixes the short name with the component: **`<component>.<short-name>`**, where `<component>` is the `# Component:` line at the top of the annotated file (also its filename). That is the form you use to set a value in **`deployment.properties`**.

Take a foundational example - the host of the upstream market-data feed. Its annotated entry, in `com.metafluent.blueprint.rtc.content.adapter.eta.properties`, is short:

```
# Bean: manager
######################
# Property: manager.etaServerHost
# Description:
#   Host name for ETA server
# [Default: eta-server-host]
#
manager.etaServerHost=eta-server-host
```

and in `deployment.properties` it is set by its fully-qualified name - the component prefix, then that same short name:

```
com.metafluent.blueprint.rtc.content.adapter.eta.manager.etaServerHost=eta-server-host
```

The per-component **settings files** list the properties a deployment commonly changes, each already fully-qualified, and `deployment.properties` carries the switches on top (which properties are promoted, and why, is [settings vs the full configurable surface](#settings-vs-the-full-configurable-surface) below). **Everything else exists only in the short-form annotated files, at its default** - but that does not put it out of reach: any setting can be overridden by adding its fully-qualified name to `deployment.properties`. Read the short name and its component from the annotated file, join them with a dot, and you have the name to set. (The session port from earlier, `server.default`, is one of these short-only settings - foundational, but not pre-listed, so its fully-qualified name appears nowhere until you write it.)

The self-report uses this same split, which is what makes the two references line up: its `bundleName` is the component and its `name` is the short name - join them with a dot for the fully-qualified name to set.

---

## Generate a live configuration report

The annotated files tell you what settings mean; the **`config` API** tells you what they are currently **set to**. One call dumps every setting in effect across every component, each with its default and resolved value, version-stamped - a complete, live report of the deployment's configuration. Save it as an artifact for the release:

```
curl -s "http://mf-api-gateway:9090/api/config/v1/*/fullProperties?bundleName=.*" \
  > elastic-mds-config-6.8.0.json
```

Each entry pins a component and its **version**. The outer array holds one element **per container** - a single consolidated container here - and each element lists that container's components:

```json
[
  [
    { "bundleName": "com.metafluent.blueprint.rtc.session.server.tcpip", "bundleVersion": "6.3.0",
      "properties": [
        { "name": "server.default",       "default": "8900",  "actual": "8900" },
        { "name": "server.networks",      "default": "$(METAFLUENT_CLIENT_NETWORKS:)", "actual": "" },
        { "name": "server.portRange",     "default": "1",     "actual": "1" } ] },

    { "bundleName": "com.metafluent.blueprint.core.utilities", "bundleVersion": "6.8.0",
      "properties": [
        { "name": "restServer.standAlone", "default": "false", "actual": "true" } ] }
  ]
]
```

This is the same content each component writes to its startup **full report** on disk (the file ending `-FullPropertiesReportXMLFile.xml`, see [Configuration: Basics](Configuration-Basics.md)) - the gateway call just gathers it across the whole deployment in one request, live. On a multi-container deployment the outer array has one element per container, which is why you narrow to a single one with `image=` (below).

**Reading an entry:**

| Field | Meaning |
|-------|---------|
| `bundleName` | The component the setting belongs to (the `<component>` half of a fully-qualified name). |
| `bundleVersion` | The component's version - what makes the entry a reference for *this* release. |
| `name` | The setting's short name (the `<short-name>` half). |
| `default` | The value shipped for this version - the reference value. |
| `actual` | What it resolved to in this deployment: the default, unless an override changed it (see [how values are assembled](Configuration-Advanced.md#how-a-deployments-configuration-is-assembled)). |

To scope the dump - by component with the `bundleName` regex, or to a single container with the `image=` predicate - see [inspecting the configuration in depth](Configuration-Advanced.md#inspecting-the-effective-configuration-in-depth).

---

## Settings vs the full configurable surface

Not every property is one you are expected to touch. A curated subset is promoted as **settings** - the properties a deployment commonly adjusts - into the per-component settings files, in fully-qualified form, each with its description and default (this is [setting values](Configuration-Basics.md)). That subset is your starting point.

Behind it is the **full configurable surface**: each property in the annotated `config/defaults/` files, and everything the self-report returns. Any of these can be overridden - add its fully-qualified name to `deployment.properties` - even if it is not promoted as a setting. Reach past the settings only when you need a property they do not cover: the annotated file gives you its meaning and default, and the self-report gives you its current value.

---

## Keeping the reference accurate across upgrades

Both references are version-stamped - the annotated file headers and every self-report entry carry the component version - so both pin to a specific release. When you upgrade:

1. Regenerate the self-report dump (or re-extract the annotated files) against the new release.
2. Diff it against the copy you saved for the previous release.

The diff shows exactly which defaults changed and which settings were added or removed between versions - the version-to-version configuration delta, straight from the product rather than from release notes.

---

## Where to go next

- [Configuration: Basics](Configuration-Basics.md) - setting values, and the on-disk configuration reports.
- [Configuration: Advanced](Configuration-Advanced.md) - how a final value is assembled, and scoping the self-report by component or container.
- [REST API](REST-API.md) - the query grammar behind the `config` calls.
- [Deployment: Basics](Deployment-Basics.md) - the deployment project where `deployment.properties` lives.
