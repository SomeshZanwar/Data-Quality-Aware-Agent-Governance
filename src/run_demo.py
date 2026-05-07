from agent_control_plane.agent_kernel import ActionType

from governed_access import governed_data_access
from audit_logger import GovernanceAuditLogger


SCENARIOS = [
    {
        "request_id": "request-001",
        "agent_id": "analyst-agent-01",
        "action_type": ActionType.DATABASE_QUERY,
        "tool": "sql_query",
        "dataset": "sales_metrics",
    },
    {
        "request_id": "request-002",
        "agent_id": "analyst-agent-01",
        "action_type": ActionType.DATABASE_QUERY,
        "tool": "sql_query",
        "dataset": "user_events",
    },
    {
        "request_id": "request-003",
        "agent_id": "analyst-agent-01",
        "action_type": ActionType.DATABASE_WRITE,
        "tool": "write_db",
        "dataset": "sales_metrics",
    },
    {
        "request_id": "request-004",
        "agent_id": "pipeline-agent-01",
        "action_type": ActionType.DATABASE_WRITE,
        "tool": "write_db",
        "dataset": "clean_pipeline_table",
    },
    {
        "request_id": "request-005",
        "agent_id": "unknown-agent-99",
        "action_type": ActionType.DATABASE_QUERY,
        "tool": "sql_query",
        "dataset": "sales_metrics",
    },
]


def print_decision(entry: dict) -> None:
    status = "ALLOWED" if entry["allowed"] else f"BLOCKED by {entry['blocked_by']}"

    print("-" * 80)
    print(f"Request ID: {entry['request_id']}")
    print(f"Agent: {entry['agent_id']}")
    print(f"Role: {entry['role']}")
    print(f"Action: {entry['action']}")
    print(f"Tool: {entry['tool']}")
    print(f"Dataset: {entry['dataset']}")
    print(f"Status: {status}")
    print(f"Reason: {entry['reason']}")

    if entry["quality_score"] is not None:
        print(f"Quality Score: {entry['quality_score']}")

    if entry["data_owner"]:
        print(f"Data Owner: {entry['data_owner']}")

    if entry["data_issues"]:
        print("Data Issues:")
        for issue in entry["data_issues"]:
            print(f"  - {issue}")


def main() -> None:
    audit_logger = GovernanceAuditLogger()

    print("=" * 80)
    print("DATA QUALITY-AWARE AGENT GOVERNANCE DEMO")
    print("=" * 80)

    for scenario in SCENARIOS:
        decision = governed_data_access(**scenario)
        entry = audit_logger.log_decision(decision)
        print_decision(entry)

    report = audit_logger.export_report("outputs/governance_report.json")

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total decisions: {report['total_decisions']}")
    print(f"Allowed: {report['allowed']}")
    print(f"Blocked: {report['blocked']}")
    print(f"Blocked by identity: {report['blocked_by_identity']}")
    print(f"Blocked by agent policy: {report['blocked_by_agent_policy']}")
    print(f"Blocked by data quality: {report['blocked_by_data_quality']}")
    print("Audit report exported to: outputs/governance_report.json")


if __name__ == "__main__":
    main()