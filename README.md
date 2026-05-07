# Data Quality-Aware Agent Governance

This project extends my [AI Data Governance Platform](https://github.com/SomeshZanwar/ai-data-governance-platform) by adding an agent-governance layer. Instead of only checking whether data is reliable, this prototype checks whether an AI agent is authorized to use that data *and* whether the data is trustworthy at the time of access.

---

## The Problem

An analyst agent has permission to query a sales dataset. The policy engine clears it — registered agent, valid action, nothing blocked.

But that morning, three dbt tests failed on the same dataset. The freshness threshold was breached by 14 hours. The quality score dropped below the minimum. The data is technically accessible, but the numbers are not trustworthy.

The agent queries it anyway. Nobody told the policy engine what the data governance system already knew.

That is the gap this project is built to make visible.

Agent governance answers: *Is this agent allowed to act?*
Data governance answers: *Is this data trustworthy right now?*

Most systems run these checks separately, in different tools, with no shared decision point. This prototype combines both into a single governance layer with a unified audit trail.

---

## How It Works

Every agent request goes through three checks in sequence. If any check fails, the request is blocked and the reason is recorded — no exceptions, no fallback.

```
Agent Request
  │
  ▼
Layer 0: Identity check
  Is this agent registered?
  Unknown agents stop here.
  │
  ▼
Layer 1: Agent policy check  [Microsoft Agent Governance Toolkit]
  Is this agent authorized for this action?
  Uses PolicyEngine, PolicyRule, AgentContext, ExecutionRequest.
  │
  ▼
Layer 2: Data quality check
  Is the target dataset fresh, validated, and above the quality threshold?
  Checks freshness, quality score, and failed validation tests.
  │
  ▼
Final decision → Unified JSON audit log
```

The policy engine from Microsoft's Agent Governance Toolkit handles Layer 1. The data quality registry — which simulates the kind of validation metadata a dbt-based governance platform would produce — handles Layer 2.

---

## Demo Scenarios

Five scenarios, covering all three failure modes and two full-pass cases:

| Request | Agent | Action | Dataset | Result | Blocked By |
|---|---|---|---|---|---|
| request-001 | analyst-agent-01 | database_query | sales_metrics | ✅ Allowed | — |
| request-002 | analyst-agent-01 | database_query | user_events | ❌ Blocked | data quality |
| request-003 | analyst-agent-01 | database_write | sales_metrics | ❌ Blocked | agent policy |
| request-004 | pipeline-agent-01 | database_write | clean_pipeline_table | ✅ Allowed | — |
| request-005 | unknown-agent-99 | database_query | sales_metrics | ❌ Blocked | identity |

### Example output

```
request-001: analyst-agent-01 → database_query on sales_metrics
Status  : ALLOWED
Reason  : Agent authorized and dataset passed quality checks.
Quality : 0.94  |  Owner: analytics-team

request-002: analyst-agent-01 → database_query on user_events
Status  : BLOCKED by data_quality
Reason  : Dataset failed quality checks.
Issues  : stale_data: last validated 26.0h ago; threshold is 12h
          failed_tests: not_null_user_id, accepted_values_event_type
Quality : 0.72  |  Owner: data-engineering

request-003: analyst-agent-01 → database_write on sales_metrics
Status  : BLOCKED by agent_policy
Reason  : policy_violation: Block analyst database writes

request-004: pipeline-agent-01 → database_write on clean_pipeline_table
Status  : ALLOWED
Reason  : Agent authorized and dataset passed quality checks.
Quality : 0.98  |  Owner: platform-team

request-005: unknown-agent-99 → database_query on sales_metrics
Status  : BLOCKED by identity
Reason  : Agent 'unknown-agent-99' is not registered.

────────────────────────────────────────
Total decisions : 5
Allowed         : 2
Blocked         : 3
  by identity   : 1
  by policy     : 1
  by data quality: 1
```

---

## Project Structure

```
data-quality-aware-agent-governance/
├── policies/
│   └── data_agent_policy.yaml        Policy intent in YAML
├── src/
│   ├── governed_access.py            Core: three-layer governance logic
│   ├── agent_policy.py               AGT policy engine + custom rules
│   ├── data_quality_registry.py      Dataset quality checks
│   ├── audit_logger.py               Unified JSON audit trail
│   └── run_demo.py                   Demo runner
├── tests/
│   └── test_governed_access.py       Tests for all three layers
├── outputs/
│   └── demo_output.txt               Reproducible demo output
├── docs/
│   └── architecture.md               Architecture and design notes
├── README.md
├── requirements.txt
└── .gitignore
```

### Key file: `src/governed_access.py`

This is the centerpiece. It calls identity verification, runs the AGT policy check, runs the data quality check, and returns a `GovernanceDecision` — a typed return structure that makes the contract explicit regardless of which layer handled the request.

The policy engine is instantiated once at module load, not on every call. This matters because `create_policy_engine()` registers custom rules — doing that per request would be equivalent to reloading a ruleset on every transaction.

---

## Tech Stack

- Python 3.10+
- [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) (`agent-os-kernel`, `agentmesh-platform`)
- `agent_control_plane` — AGT's kernel layer for `AgentContext`, `ExecutionRequest`, `PolicyRule`, `ActionType`, `PermissionLevel`
- YAML policy definitions
- JSON audit logging
- pytest for governance layer tests

---

## How to Run

```bash
# Create and activate a virtual environment
python -m venv agt-env
source agt-env/bin/activate      # Mac/Linux
# agt-env\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Run the demo
python src/run_demo.py

# Run tests
python -m pytest tests/ -v
```

The demo writes a governance audit report to `outputs/governance_report.json`.

---

## What the Data Quality Registry Simulates

The registry in `data_quality_registry.py` simulates the kind of metadata a dbt-based governance platform would expose at runtime. For each dataset it tracks:

- **Freshness** — how long ago was this dataset last validated, and what is the threshold?
- **Quality score** — a composite score from 0 to 1, compared against a per-dataset minimum
- **Failed tests** — specific validation test names that did not pass (e.g., `not_null_user_id`)
- **Data owner** — the team responsible, surfaced in blocked decisions so the requester knows who to contact

A production version would pull this from real dbt test results, a metadata catalog, or a data observability platform like Monte Carlo or Metaplane.

---

## Connection to My AI Data Governance Platform

My [AI Data Governance Platform](https://github.com/SomeshZanwar) focuses on the data side: dbt-based transformations, PostgreSQL metadata storage, governance-ready reporting layers, and data quality checks.

This project adds the agent side: what happens when an AI agent tries to act on that data. The two layers together answer the question that either one alone cannot: *Is this agent allowed to use this data, and is this data worth using right now?*

---

## Current Limitations

This is a prototype. The data quality registry is simulated in Python rather than connected to a live governance system. The agent identity store is a hardcoded dict rather than a real identity provider.

A production version would integrate with:
- dbt test results and metadata via dbt Cloud API or dbt artifacts
- A metadata catalog (Datahub, Atlan, or similar) for dataset ownership and lineage
- A data observability platform for real-time quality signals
- A real identity provider for agent authentication

---

## Potential Open-Source Contribution

I am exploring adding a simplified version of this two-layer governance pattern as an example contribution to Microsoft's Agent Governance Toolkit under `examples/data-quality-aware-governance/`. The discussion is tracked in [CONTRIBUTION_PLAN.md](CONTRIBUTION_PLAN.md).
