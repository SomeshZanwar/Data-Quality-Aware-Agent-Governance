# Open-Source Contribution Plan

This document outlines a planned contribution to Microsoft's Agent Governance Toolkit based on this portfolio project.

## Goal

Propose a small example showing how agent authorization can be combined with external data quality signals before allowing an agent action.

## Proposed Contribution Type

Example contribution, not a core package change.

Proposed location in the upstream repository:

```text
examples/data-quality-aware-governance/
```

## Proposed Files

```text
examples/data-quality-aware-governance/
  README.md
  data_quality_policy_example.py
  sample_policy.yaml
  expected_output.txt
```

## Pattern Demonstrated

The example would show a two-layer governance decision:

1. Agent policy evaluation - Is the agent authorized to perform the action?
2. Data quality validation - Is the target dataset fresh, validated, and trustworthy?

Final decision:

```text
allow only if both checks pass
```

## Example Scenario

```text
Agent: analyst-agent-01
Action: database_query
Dataset: user_events
```

Agent policy result:

```text
allowed
```

Data quality result:

```text
blocked because dataset is stale, has a low quality score, and has failed validation tests
```

Final decision:

```text
blocked by data_quality
```

## Why This Could Help the Upstream Project

The Agent Governance Toolkit focuses on governing agent behavior, policy enforcement, identity, compliance, and auditability.

Data and analytics agents often need an additional trust signal: whether the data being accessed is reliable at the time of access.

This example would demonstrate how AGT policy checks can be composed with external governance signals such as:

- data freshness
- validation test status
- quality score
- dataset ownership
- audit logging

## Contribution Sequence

1. Finish and polish this portfolio project.
2. Star the Microsoft Agent Governance Toolkit repository.
3. Review existing issues and discussions.
4. Engage with one or two relevant discussions if possible.
5. Open a discussion proposing the data-quality-aware governance example.
6. Submit an example pull request only if maintainers indicate that the pattern fits the project direction.

GitHub Discussion: https://github.com/microsoft/agent-governance-toolkit/discussions/1795

Status: PR #1818 merged by @imran-siddique into microsoft:main — May 2026

## Draft Discussion Title

```text
Example proposal: Data quality-aware agent policy evaluation
```

## Draft Discussion Body

I have been exploring the Agent Governance Toolkit for data and analytics agent use cases. One pattern I found useful is combining agent authorization with dataset trust signals before allowing an action.

Current policy checks can determine whether an agent is allowed to perform an action such as a database query. In data governance workflows, there is often another required check: whether the target dataset is fresh, validated, and trustworthy at the time of access.

Example scenario:

- Agent is authorized to run database queries
- Target dataset failed freshness or quality checks
- Final governance decision should block the action, even though agent authorization passed

Would the maintainers be open to an example under `examples/` demonstrating this pattern with:

- AGT policy evaluation
- simulated data quality registry
- final allow/block decision
- JSON audit output

I can prepare a small Python example if this fits the project direction.
