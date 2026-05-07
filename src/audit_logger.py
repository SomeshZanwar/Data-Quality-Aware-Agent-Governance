import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class GovernanceAuditLogger:
    """
    Unified audit logger for agent authorization and data quality decisions.
    """

    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    def log_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": decision["request_id"],
            "agent_id": decision["agent_id"],
            "role": decision["role"],
            "action": decision["action"],
            "tool": decision["tool"],
            "dataset": decision["dataset"],
            "allowed": decision["allowed"],
            "blocked_by": decision["blocked_by"],
            "reason": decision["reason"],
            "quality_score": decision["quality_score"],
            "data_owner": decision["data_owner"],
            "data_issues": decision["data_issues"],
        }

        self.entries.append(entry)
        return entry

    def build_report(self) -> Dict[str, Any]:
        return {
            "generated_at": datetime.now().isoformat(),
            "total_decisions": len(self.entries),
            "allowed": len([entry for entry in self.entries if entry["allowed"]]),
            "blocked": len([entry for entry in self.entries if not entry["allowed"]]),
            "blocked_by_identity": len(
                [entry for entry in self.entries if entry["blocked_by"] == "identity"]
            ),
            "blocked_by_agent_policy": len(
                [entry for entry in self.entries if entry["blocked_by"] == "agent_policy"]
            ),
            "blocked_by_data_quality": len(
                [entry for entry in self.entries if entry["blocked_by"] == "data_quality"]
            ),
            "entries": self.entries,
        }

    def export_report(self, filepath: str) -> Dict[str, Any]:
        report = self.build_report()

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2)

        return report