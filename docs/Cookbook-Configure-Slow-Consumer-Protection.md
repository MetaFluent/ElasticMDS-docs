# Configuration Cookbook: Slow Consumer Protection

Elastic MDS protects a slow consumer in two ways: it automatically adapts connection resources to a consumer's needs and, if so configured, will conflate updates to protect the consumer from I/O overflows. Delivery scaling is on by default; conflation applies only to the consumers you assign a rule to. This page covers configuring both.

For the concepts behind these two mechanisms, see [Slow-consumer protection: delivery scaling and conflation](Architecture-Advanced.md#slow-consumer-protection-delivery-scaling-and-conflation).

**Audience:** Operator.
**Prerequisites:** a running deployment with orchestration and a push distribution server serving client sessions.

---

## Delivery scaling

Delivery scaling has default settings, so nothing needs to be set for it to work. Change these settings to adjust how aggressively a deployment adds resources for a slow consumer, or how long it waits before taking them back.

These settings are in the orchestration service's adaptive result policy, read at startup from:

```
deployment-config/resources/orchestration/policies/result/adaptive-result-policy.json
```

| Setting | Default | What it controls |
|-------|---------|-------------------|
| `MaxShardsPerTarget` | 5 | The overall ceiling on how many delivery shards any one consumer's result can be split across. |
| `ConcernSplitMaxShardsPerTarget` | 2 | Within that ceiling, the most extra shards that may be added specifically to relieve a single slow consumer. |
| `SplitLoadThresholdSlowPercent` | 45 | How heavily loaded a consumer must be - as a percent of the rate it can sustain - before it is given extra shards, for a consumer that has already been running slow. Lower means it scales in earlier. |
| `SplitLoadThresholdFastPercent` | 70 | The same threshold for a consumer that has been keeping up well until now. Higher than the slow threshold, so a fast consumer is given the benefit of the doubt longer before extra shards are added. |
| `DuressDrainSpeedupFactor` | 2 | How much faster content moves onto a new shard while it is actively relieving a slow consumer, compared with normal rebalancing (2 means twice the normal speed). |
| `DuressCooldownSeconds` | 30 | How long a consumer must stay within its limit before the extra resource added for it is taken back. |
| `ShardRebalanceTimeSeconds` | 10 | Normal rebalance pacing, outside of relieving a slow consumer. |
| `ScaleDownDrainTickMillis` | 250 | Normal scale-down pacing, outside of relieving a slow consumer. |

An example policy with every setting specified:

```json
{
  "ResultPolicyType": "AdaptiveResultPolicy",
  "Policy": {
    "Name": "adaptive-result-policy",
    "MaxShardsPerTarget": 5,
    "ConcernSplitMaxShardsPerTarget": 2,
    "SplitLoadThresholdSlowPercent": 45,
    "SplitLoadThresholdFastPercent": 70,
    "ShardRebalanceTimeSeconds": 10,
    "ScaleDownDrainTickMillis": 250,
    "DuressDrainSpeedupFactor": 2,
    "DuressCooldownSeconds": 30
  }
}
```

## Conflation rules

Conflation of updates is a last resort to avoid connection overflow and results in degradation of tick-by-tick updates to conflated updates.

Conflation rules control per-session conflation on the push distribution server: which updates are collapsed, and the thresholds at which automatic conflation engages, for the consumers a rule is assigned to. A consumer with no matching rule is not conflated - it still gets delivery scaling, above.

Rules are read from a single JSON file. This section documents that file and its fields.

### File location

Rules are read at startup from:

```
deployment-config/resources/conflation-rules/rules.json
```

A `rules.json.txt` in the same directory holds the examples below. It is not loaded at runtime; only `rules.json` is read.

### File format

The file is a JSON object with three members:

| Member | Type | Purpose |
|--------|------|---------|
| `expressions` | name to string | Named conflation expressions. |
| `policies` | name to object | Named engagement policies. |
| `rules` | array | Match criteria plus references to one expression and one policy. |

`expressions` and `policies` are reusable libraries; a rule references entries by name. Unreferenced entries are permitted. Referencing a name that is not defined is a configuration error and fails at load.

#### expressions

An expression defines the contents of a conflated update. Any valid SQL function expression can be used.

| Name | Expression | Effect |
|------|-----------|--------|
| `250ms` | `MFUtil.UPDATED(MFUtil.TIMER(250, 'MILLISECONDS'))` | At most one update per 250 ms. |
| `250msORtrade` | `MFUtil.UPDATED(MFUtil.TIMER(250, 'MILLISECONDS'), TRDPRC_1)` | At most one update per 250 ms; always emit on a `TRDPRC_1` change. |

#### policies

A policy holds the thresholds at which automatic conflation engages and disengages for a matching session. Three are shipped:

| Policy | `highWaterFraction` | Engagement |
|--------|---------------------|------------|
| `conservative` | 0.35 | earliest |
| `default` | 0.65 | balanced |
| `aggressive` | 0.85 | latest |

- `highWaterFraction` - fraction of a consumer's estimated capacity at which conflation engages. Lower engages sooner.
- `lowWaterFraction` - fraction at which conflation disengages.

Full values are in the [complete file](#complete-file) below.

#### rules

Each rule is an object:

| Field | Required | Meaning |
|-------|----------|---------|
| `ApplicationId`, `UserId`, `PositionPrefix`, `Catalog`, `Schema`, `TableName` | no | Match criteria. An omitted field matches any value. A rule with no match fields matches every session. |
| `Expression` | no | Name of an entry in `expressions`. Omit to match a session without conflating it. |
| `ConcernLevelPolicy` | no | Name of an entry in `policies`. |
| `Priority` | no | Integer; lower wins. Omitted defaults to `0` (highest precedence). |

### Examples

#### Catch-all

```json
{ "Expression": "250msORtrade", "ConcernLevelPolicy": "default", "Priority": 100 }
```

No match fields, so it applies to every session: at most one update per 250 ms, trades always emitted, `default` policy. `Priority` is set to 100 so more specific rules override it.

#### Disable conflation for an application

```json
{ "ApplicationId": "algo-execution", "Priority": 10 }
```

No `Expression`, so matching sessions are not conflated - they still get delivery scaling, which needs no rule. `Priority` 10 is lower than the catch-all's 100, so this rule applies to `algo-execution` sessions.

#### Different expression and policy for a user

```json
{ "UserId": "wan-consumer", "Expression": "1000msORtrade", "ConcernLevelPolicy": "conservative", "Priority": 50 }
```

All sessions for the user `wan-consumer` get a one-second cadence under `conservative`. `Priority` 50 is below the catch-all (100) and above the application rule (10).

Resolution for these three rules: ordinary sessions get 250 ms / `default`; `algo-execution` is not conflated (delivery scaling still protects it); `wan-consumer` gets 1000 ms / `conservative`.

### Priority

When more than one rule matches a session, the rule with the lowest `Priority` applies. An omitted `Priority` is `0`, the highest precedence. Set a high number on broad rules and low numbers on the exceptions that override them.

### Complete file

```json
{
  "expressions": {
    "250ms":         "MFUtil.UPDATED(MFUtil.TIMER(250, 'MILLISECONDS'))",
    "250msORtrade":  "MFUtil.UPDATED(MFUtil.TIMER(250, 'MILLISECONDS') ,TRDPRC_1)",
    "1000ms":        "MFUtil.UPDATED(MFUtil.TIMER(1000, 'MILLISECONDS'))",
    "1000msORtrade": "MFUtil.UPDATED(MFUtil.TIMER(1000, 'MILLISECONDS') ,TRDPRC_1)"
  },
  "policies": {
    "conservative": { "highWaterFraction": 0.35, "lowWaterFraction": 0.15 },
    "default":      { "highWaterFraction": 0.65, "lowWaterFraction": 0.35 },
    "aggressive":   { "highWaterFraction": 0.85, "lowWaterFraction": 0.50 }
  },
  "rules": [
    { "Expression": "250msORtrade", "ConcernLevelPolicy": "default", "Priority": 100 },
    { "ApplicationId": "algo-execution", "Priority": 10 },
    { "UserId": "wan-consumer", "Expression": "1000msORtrade", "ConcernLevelPolicy": "conservative", "Priority": 50 }
  ]
}
```

Copy this file, or individual entries from `rules.json.txt`, into `deployment-config/resources/conflation-rules/rules.json`.

---

## Verify

**Delivery scaling.** Ask orchestration how many shards are currently serving each result - more than one means Elastic MDS has scaled that consumer's delivery:

```
curl -s "http://mf-api-gateway:9090/api/orchestration/v1/sessions/*/statements/*/results/*/shards/*/shardID"
```

**Conflation rules.** List the loaded rules:

```
curl -s http://mf-api-gateway:9090/api/conflation-rules/v1/rules
```

Each rule reports its `policyName`. Inspect the named libraries and individual entries:

```
curl -s http://mf-api-gateway:9090/api/conflation-rules/v1/policies
curl -s http://mf-api-gateway:9090/api/conflation-rules/v1/policies/conservative
curl -s http://mf-api-gateway:9090/api/conflation-rules/v1/expressions
curl -s http://mf-api-gateway:9090/api/conflation-rules/v1/expressions/250msORtrade
```

**On a running connection.** The push distribution server reports, per shard, whether conflation is currently engaged:

```
curl -s "http://mf-api-gateway:9090/api/push-distribution-server/v1/*/shards/autoConflationEngaged=true/shardID,offeredUpdates"
```

---

## Where to go next

- [Architecture: Advanced](Architecture-Advanced.md#slow-consumer-protection-delivery-scaling-and-conflation) - the mechanism behind both protections.
- [Monitoring & Diagnostics](Operations-Monitoring.md#resource-monitoring) - watching shard counts and conflation status on a running deployment.
- [Troubleshooting & FAQ](Operations-Troubleshooting.md) - reading a slow-consumer signal when you see one.
- [REST API](REST-API.md) - the full query surface these `curl` examples are built from.
