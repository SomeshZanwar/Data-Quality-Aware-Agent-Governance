from datetime import datetime, timedelta
from typing import Dict, Any


DATA_QUALITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sales_metrics": {
        "last_validated": datetime.now() - timedelta(hours=2),
        "freshness_threshold_hours": 6,
        "quality_score": 0.94,
        "minimum_quality_score": 0.85,
        "owner": "analytics-team",
        "failed_tests": [],
    },
    "user_events": {
        "last_validated": datetime.now() - timedelta(hours=26),
        "freshness_threshold_hours": 12,
        "quality_score": 0.72,
        "minimum_quality_score": 0.85,
        "owner": "data-engineering",
        "failed_tests": ["not_null_user_id", "accepted_values_event_type"],
    },
    "clean_pipeline_table": {
        "last_validated": datetime.now() - timedelta(hours=1),
        "freshness_threshold_hours": 4,
        "quality_score": 0.98,
        "minimum_quality_score": 0.90,
        "owner": "platform-team",
        "failed_tests": [],
    },
}


def check_data_quality(dataset_name: str) -> Dict[str, Any]:
    """
    Check whether a dataset is trustworthy enough for agent use.
    """
    dataset = DATA_QUALITY_REGISTRY.get(dataset_name)

    if not dataset:
        return {
            "trustworthy": False,
            "blocked_by": "data_quality",
            "reason": f"Dataset '{dataset_name}' not found in data quality registry.",
            "issues": ["dataset_not_registered"],
            "owner": None,
            "quality_score": None,
        }

    issues = []

    hours_since_validation = (
        datetime.now() - dataset["last_validated"]
    ).total_seconds() / 3600

    if hours_since_validation > dataset["freshness_threshold_hours"]:
        issues.append(
            f"stale_data: last validated {hours_since_validation:.1f}h ago; "
            f"threshold is {dataset['freshness_threshold_hours']}h"
        )

    if dataset["quality_score"] < dataset["minimum_quality_score"]:
        issues.append(
            f"low_quality_score: {dataset['quality_score']} below minimum "
            f"{dataset['minimum_quality_score']}"
        )

    if dataset["failed_tests"]:
        issues.append(
            f"failed_tests: {', '.join(dataset['failed_tests'])}"
        )

    return {
        "trustworthy": len(issues) == 0,
        "blocked_by": "data_quality" if issues else None,
        "reason": "Dataset passed quality checks." if not issues else "Dataset failed quality checks.",
        "issues": issues,
        "owner": dataset["owner"],
        "quality_score": dataset["quality_score"],
    }