# Data Quality-Aware Agent Governance

This project extends my AI Data Governance Platform by adding an agent-governance layer. Instead of only checking whether data is reliable, this prototype checks whether an AI agent is authorized to use that data and whether the data is trustworthy at the time of access.

## Problem

Agent governance systems answer one important question:

> Is this agent allowed to perform this action?

Data governance systems answer a different question:

> Is this dataset reliable enough to use?

The risk appears when these two checks are separated. An agent may be authorized to query a dataset, but that dataset may have failed freshness, quality, or validation checks earlier that day.

This project bridges that gap.

## What This Project Does

This prototype enforces a three-step governance flow:

1. Agent identity check - Is the agent registered?
2. Agent policy check - Is the agent authorized to perform this action?
3. Data quality check - Is the target dataset trustworthy right now?

An agent action is allowed only when all three checks pass.

## Demo Scenarios

| Request | Agent | Action | Dataset | Result |
|---|---|---|---|---|
| request-001 | analyst-agent-01 | database_query | sales_metrics | Allowed |
| request-002 | analyst-agent-01 | database_query | user_events | Blocked by data quality |
| request-003 | analyst-agent-01 | database_write | sales_metrics | Blocked by agent policy |
| request-004 | pipeline-agent-01 | database_write | clean_pipeline_table | Allowed |
| request-005 | unknown-agent-99 | database_query | sales_metrics | Blocked by identity |

## Architecture

```text
Agent Request
  -> Identity Verification
  -> Microsoft Agent Governance Toolkit Policy Check
  -> Data Quality Registry Check
  -> Final Allow / Block Decision
  -> Unified JSON Audit Log
```

## Project Structure

```text
data-quality-aware-agent-governance/
  policies/
    data_agent_policy.yaml
  src/
    agent_policy.py
    audit_logger.py
    data_quality_registry.py
    governed_access.py
    run_demo.py
  outputs/
    .gitkeep
  README.md
  requirements.txt
  .gitignore
```

## Key Files

### src/governed_access.py

This is the centerpiece of the project. It combines identity verification, agent policy evaluation, data quality validation, and the final governance decision.

### src/agent_policy.py

Creates the Microsoft Agent Governance Toolkit policy engine and registers a custom rule that blocks analyst agents from database writes.

### src/data_quality_registry.py

Simulates a data governance layer with freshness thresholds, quality scores, failed tests, and data ownership metadata.

### src/audit_logger.py

Creates a unified JSON audit trail for identity blocks, agent policy blocks, data quality blocks, and allowed actions.

### src/run_demo.py

Runs the full demo across five governance scenarios.

## Example Output

```text
request-001: analyst-agent-01 queries sales_metrics
Status: ALLOWED
Reason: Agent authorized and dataset passed quality checks.

request-002: analyst-agent-01 queries user_events
Status: BLOCKED by data_quality
Reason: Dataset failed quality checks.

request-003: analyst-agent-01 writes to sales_metrics
Status: BLOCKED by agent_policy
Reason: policy_violation: Block analyst database writes

request-004: pipeline-agent-01 writes to clean_pipeline_table
Status: ALLOWED
Reason: Agent authorized and dataset passed quality checks.

request-005: unknown-agent-99 queries sales_metrics
Status: BLOCKED by identity
Reason: Agent 'unknown-agent-99' is not registered.
```

## Tech Stack

- Python
- Microsoft Agent Governance Toolkit
- agent-os-kernel
- agentmesh-platform
- YAML policy definitions
- JSON audit logging

## How to Run

Create and activate a virtual environment:

```bash
python -m venv agt-env
agt-env\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the demo:

```bash
python src/run_demo.py
```

The demo exports a governance audit report to:

```text
outputs/governance_report.json
```

## Why This Matters

Most governance examples focus on either agent permissions or data quality. This project combines both.

The final decision is not based only on whether the agent is allowed. It also depends on whether the data is trustworthy at the time of access.

That matters for analytics agents, BI copilots, data pipeline agents, and any system where AI agents interact with business data.

## Future Improvements

- Connect the data quality registry to real dbt test results
- Add lineage-aware dataset checks
- Add delegation chain tracking for multi-agent workflows
- Add a dashboard for governance decisions over time
- Convert this pattern into an example contribution for Microsoft's Agent Governance Toolkit
