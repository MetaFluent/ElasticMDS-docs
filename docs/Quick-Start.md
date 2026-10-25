# Quick Start

This guide takes you from nothing to a **running Elastic MDS system streaming simulated market data**, on a single machine, in about 20 minutes. You will start the system, confirm it is healthy, and watch a stream of simulated data arrive at a subscribing client.

Elastic MDS is a set of cooperating services. This guide runs them together on one machine using Docker Compose, because that is the quickest way to get going - but the services are not tied to Compose, or to any one machine (more on that below).

> **What this is - and what it isn't.** By default, this Quick Start brings up the same services, in the same shape, that a real Elastic MDS deployment runs - just on a single host, fed by a simulator instead of a live market-data feed. The simulator is the one throwaway piece; swap in a real ETA feed and what you built here keeps running. From there you grow out, not start over - more projectors, more hosts, redundancy - see [Fine-Grained](Cookbook-Deploy-Fine-Grained.md), [Scalable MDS](Cookbook-Deploy-Scalable.md), or **[Deployment: Basics](Deployment-Basics.md)** for the full picture. (Took the [Demo](Cookbook-Deploy-Demo.md) path in Step 3 instead? That one is the pure evaluation peek - a single all-in-one image, not the deployment shape.)

**Audience:** anyone getting Elastic MDS running for the first time - whether you are already a MetaFluent user or brand new. No prior MetaFluent knowledge assumed.

---

## Before you begin

You need four things. The first two are generic; follow the linked instructions if you do not already have them.

| # | Requirement | How to get it |
|---|-------------|---------------|
| 1 | **A Linux host** with a shell. | Any modern Linux distribution. (macOS or Windows with Docker Desktop also work; the commands are the same, but this guide assumes Linux.) |
| 2 | **Docker Engine + the Docker Compose plugin.** | Follow Docker's official install guide: <https://docs.docker.com/engine/install/>. Then verify: `docker --version` and `docker compose version` should both print a version. |
| 3 | **A GitHub account with access to your MetaFluent organization.** | MetaFluent provides your team a private GitHub organization, `MetaFluent-Dist-NN`, holding the deployment projects, SDKs, installation packages, and container images (`NN` is the number you are given when your access is set up). Sign in with your own GitHub account (sign up at <https://github.com/join> if you do not have one) and accept the invitation emailed to you. Access to the images follows automatically. See [Deployment: Basics](Deployment-Basics.md#your-metafluent-github-organization). |
| 4 | **A GitHub Personal Access Token (PAT)** with the `read:packages` scope. | Create a classic PAT: <https://github.com/settings/tokens>. Tick **`read:packages`**. Copy the token somewhere safe - you cannot view it again. |

---

## Step 1 - Log in to the image registry

Elastic MDS images are published to the GitHub Container Registry, `ghcr.io`. Authenticate Docker to it once, using the PAT from requirement 4:

```
export CR_PAT=<your-personal-access-token>
echo "$CR_PAT" | docker login ghcr.io -u <your-github-username> --password-stdin
```

You should see `Login Succeeded`.

> **Stuck here?** If you see `denied` or `unauthorized`, the login worked but your account cannot see the images yet - that is an access grant, not a Docker problem. Confirm you accepted the invitation to your `MetaFluent-Dist-NN` organization (requirement 3), then try again. This is the single most common place newcomers get stuck, so it is worth getting right before moving on.

---

## Step 2 - Set up the gateway hostname

Everything you do to monitor an Elastic MDS system - checking health, reading statistics, controlling it - goes through its **API gateway**. Across the documentation, and in real deployments, the gateway is addressed by a stable convention name: **`mf-api-gateway`**. Map that name to your own system now, before you start anything, so the same commands work here and everywhere else:

```
echo "127.0.0.1 mf-api-gateway" | sudo tee -a /etc/hosts
```

This `/etc/hosts` entry is all you need for this single-machine demo. For a permanent, network-wide mapping - a real DNS entry rather than a hosts file - see [Setting up a DNS entry for your API Gateway](Deployment-Basics.md#setting-up-a-dns-entry-for-your-api-gateway).

**Why this matters.** Using the convention name (rather than `localhost`) means every gateway command in this guide, in the rest of the docs, and the built-in tools such as `sim-ctl` - which is hardwired to `mf-api-gateway:9090` - all work unchanged, here and when you later move to a multi-container or production deployment. It is a small step that keeps your commands portable.

**If you skip it.** You can substitute `localhost` for `mf-api-gateway` in the commands below and the basic checks still work - but tools hardwired to the convention name will not, until you add the mapping. Do it now and you will not have to think about it again.

---

## Step 3 - Get the system

Which path fits depends on where you are coming from:

- **Upgrading from an existing MetaFluent product, or already a MetaFluent user?** Follow [Static MDS](Cookbook-Deploy-Static-MDS.md#docker-static-mds)'s Docker section, then add the simulator from its [Use a simulator](Cookbook-Deploy-Static-MDS.md#use-a-simulator) section, so there is data to watch in Step 6. Save that compose file into a working directory, stay there, and continue at Step 4. This is the default path, and the rest of this guide follows it.
- **New to MetaFluent and comfortable with Docker?** Follow the [Demo](Cookbook-Deploy-Demo.md#docker-demo) Docker section instead, then pick back up at Step 4 - the rest of this guide works either way, with the differences called out as you go.

---

## Step 4 - Start the system

Compose needs to know which host user account owns the files the containers write. Set that, then bring everything up:

```
export METAFLUENT_HOST_UID=$(id -u)
docker compose up -d
```

The **first** run downloads the images from `ghcr.io`, so it takes a few minutes; later runs start in seconds. When the command returns, every container is launching.

---

## Step 5 - Confirm it is healthy

Ask the gateway for the state of every component in the deployment. The gateway lets you project just the fields you care about by listing them after the resource - here, each component's name, role, state, and a one-line status:

```
curl -s http://mf-api-gateway:9090/api/application-state/v1/*/name,role,state,info
```

A healthy system responds like this - one entry per component, every one `FULLY_OPERATIONAL`:

```json
[
    { "name": "mf-api-gateway",         "role": "n/a",    "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-admin",               "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-core-srvcs",          "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-projector-mds-bpipe", "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-projector-mds-other", "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" },
    { "name": "mf-eta-simulator",       "role": "ACTIVE", "state": "FULLY_OPERATIONAL", "info": "All constituents fully operational" }
]
```

The gateway shows `role: n/a` - it has no active/standby role, so that is normal, not a problem. Everything else shows `ACTIVE` because nothing here is running redundantly yet.

(Took the [Demo](Cookbook-Deploy-Demo.md) path instead? You will see just `mf-mds-consolidated` and `mf-eta-simulator` here - the same check, on the two-image setup.)

You are looking for `state: FULLY_OPERATIONAL` on every component, including the `mf-eta-simulator`. If you see that, your Elastic MDS is up. (Drop the `/name,role,state,info` suffix to see the full detail for each component - host, image, memory and CPU stats, and its state history.)

> If the command returns nothing or connection-refused, give it another few seconds (the first startup does the most work), then retry. Persistent failures usually trace back to Step 1 (image access) - check the container logs with `docker compose logs`.

---

## Step 6 - Watch the data

The sample applications ship in the **MetaFluent JMS SDK**. Clone the current milestone (the `stable` branch) and run the prebuilt subscriber (no build needed), asking for a single instrument - here, Vodafone on the simulated `RDF` service:

```
git clone --depth 1 -b stable git@github.com:MetaFluent-Dist-NN/jms-sdk.git
cd jms-sdk
java -cp "bin/SimpleSubscriberApplication.jar:lib/*" \
     com.metafluent.examples.simplesub.SimpleSubscriber \
     -connect localhost:8900 -context com.metafluent.jms_context.mds RDF.VOD.L
```

You will see an `Image:` line - a full snapshot of the instrument's current field values - followed by `UPDATE:` lines as the simulated data changes. Press `Ctrl+C` to stop.

To learn the subscription model - contexts, topics, message types, and how your existing MetaFluent v5 JMS code carries over unchanged - see **[JMS Application Development](Develop-JMS.md)**.

---

## Step 7 - Stop the system

From the working directory where you saved `docker-compose.yml`:

```
docker compose down
```

For a completely clean slate before a fresh run, also clear the working directories:

```
rm -rf logs/* data/*
```

---

## Where to go next

- **[Architecture: Basics](Architecture-Basics.md)** - the mental model: what just happened, and the handful of concepts everything builds on.
- **[JMS Application Development](Develop-JMS.md)** - write your own subscribing or publishing application. If you have MetaFluent v5 code, start here - it still works.
- **[Deployment: Basics](Deployment-Basics.md)** - how this single-host deployment grows into a full production layout, at your own pace.
- **[Operations: Monitoring & Diagnostics](Operations-Monitoring.md)** - seeing what a running system is doing.

---

## Growing this into a full deployment

If you followed the Static MDS path above, you already have the real deployment shape: the same services this guide just ran, on a single host, with a simulator standing in for a live feed. Growing it from here does not change that shape - swap the simulator for a real ETA feed, add projectors for throughput or resilience, and spread services across machines as you need to. **[Fine-Grained](Cookbook-Deploy-Fine-Grained.md)** and **[Scalable MDS](Cookbook-Deploy-Scalable.md)** cover the next steps; **[Deployment: Basics](Deployment-Basics.md)** covers the full model.

Followed the [Demo](Cookbook-Deploy-Demo.md) path instead? **[Static MDS](Cookbook-Deploy-Static-MDS.md)** is where you pick up the real deployment shape.
