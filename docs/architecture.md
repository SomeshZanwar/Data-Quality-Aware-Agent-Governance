# Architecture Notes

## Purpose

This project demonstrates a small governance bridge between agent authorization and data trustworthiness.

Agent governance decides whether an agent is allowed to perform an action. Data governance decides whether the target dataset is reliable enough to use. This prototype combines both checks before allowing an agent action.

## Governance Flow

```text
Agent Request
  -> Identity Check
  -> Agent Policy Check
  -> Data Quality Check
  -> Final Decision
  -> Unified Audit Log
```

## Layers

### 1. Identity Check

The system first checks whether the agent is registered.

If the agent is unknown, the request is blocked before policy or data quality checks run.

### 2. Agent Policy Check

The project uses Microsoft Agent Governance Toolkit's PolicyEngine and a custom PolicyRule.

Current rule:

```text
Analyst agents can query data, but cannot write to databases.
```

### 3. Data Quality Check

The data quality registry checks:

- freshness
- quality score
- failed validation tests
- dataset ownership

If the dataset is stale, low quality, or failed tests, the request is blocked.

### 4. Unified Audit Log

Every decision is logged with:

- request ID
- agent ID
- role
- action
- dataset
- allow/block status
- block reason
- data owner
- quality score
- data issues

## Current Limitations

This is a prototype. The data quality registry is simulated in Python.

A production version would connect this layer to real governance systems such as:

- dbt test results
- metadata catalogs
- lineage tools
- data observability platforms
- access management systems
