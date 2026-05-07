"""
Tests for governed_access.py

Run with:
    python -m pytest tests/ -v

These tests verify the three governance layers independently and together.
Each test name describes the exact scenario so the output is readable
without looking at the test body.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from agent_control_plane.agent_kernel import ActionType
from governed_access import governed_data_access


# ---------------------------------------------------------------------------
# Layer 0: Identity checks
# ---------------------------------------------------------------------------

class TestIdentityLayer:

    def test_unknown_agent_is_blocked_before_policy_runs(self):
        decision = governed_data_access(
            request_id="test-identity-001",
            agent_id="unknown-agent-99",
            action_type=ActionType.DATABASE_QUERY,
            tool="sql_query",
            dataset="sales_metrics",
        )
        assert decision["allowed"] is False
        assert decision["blocked_by"] == "identity"
        assert "not registered" in decision["reason"]

    def test_unknown_agent_does_not_reach_data_quality_check(self):
        """
        Identity block should short-circuit — data_issues should be empty
        because the data quality layer never ran.
        """
        decision = governed_data_access(
            request_id="test-identity-002",
            agent_id="unknown-agent-99",
            action_type=ActionType.DATABASE_QUERY,
            tool="sql_query",
            dataset="user_events",
        )
        assert decision["blocked_by"] == "identity"
        assert decision["data_issues"] == []
        assert decision["quality_score"] is None


# ---------------------------------------------------------------------------
# Layer 1: Agent policy checks
# ---------------------------------------------------------------------------

class TestAgentPolicyLayer:

    def test_analyst_database_write_is_blocked_by_policy(self):
        decision = governed_data_access(
            request_id="test-policy-001",
            agent_id="analyst-agent-01",
            action_type=ActionType.DATABASE_WRITE,
            tool="write_db",
            dataset="sales_metrics",
        )
        assert decision["allowed"] is False
        assert decision["blocked_by"] == "agent_policy"

    def test_analyst_database_write_block_does_not_reach_data_quality(self):
        """
        Policy block should short-circuit — data quality layer should not run
        when the agent is unauthorized for the action type.
        """
        decision = governed_data_access(
            request_id="test-policy-002",
            agent_id="analyst-agent-01",
            action_type=ActionType.DATABASE_WRITE,
            tool="write_db",
            dataset="sales_metrics",
        )
        assert decision["blocked_by"] == "agent_policy"
        assert decision["data_issues"] == []

    def test_pipeline_agent_database_write_passes_policy(self):
        """
        pipeline-agent-01 has READ_WRITE permission. This should pass
        policy and reach the data quality layer.
        """
        decision = governed_data_access(
            request_id="test-policy-003",
            agent_id="pipeline-agent-01",
            action_type=ActionType.DATABASE_WRITE,
            tool="write_db",
            dataset="clean_pipeline_table",
        )
        # Policy passes — result depends on data quality
        assert decision["blocked_by"] != "agent_policy"


# ---------------------------------------------------------------------------
# Layer 2: Data quality checks
# ---------------------------------------------------------------------------

class TestDataQualityLayer:

    def test_analyst_query_on_stale_dataset_is_blocked_by_data_quality(self):
        """
        user_events is configured with failed tests and stale data.
        The analyst is authorized to query, but data quality blocks it.
        """
        decision = governed_data_access(
            request_id="test-quality-001",
            agent_id="analyst-agent-01",
            action_type=ActionType.DATABASE_QUERY,
            tool="sql_query",
            dataset="user_events",
        )
        assert decision["allowed"] is False
        assert decision["blocked_by"] == "data_quality"
        assert len(decision["data_issues"]) > 0

    def test_data_quality_block_includes_issue_details(self):
        """
        When data quality blocks a request, the decision should include
        enough detail for the requester to understand why and who owns the data.
        """
        decision = governed_data_access(
            request_id="test-quality-002",
            agent_id="analyst-agent-01",
            action_type=ActionType.DATABASE_QUERY,
            tool="sql_query",
            dataset="user_events",
        )
        assert decision["data_owner"] is not None
        assert decision["quality_score"] is not None
        assert any("stale_data" in issue or "failed_tests" in issue
                   for issue in decision["data_issues"])


# ---------------------------------------------------------------------------
# Full pass: both layers clear
# ---------------------------------------------------------------------------

class TestFullPassScenarios:

    def test_analyst_query_on_fresh_trusted_dataset_is_allowed(self):
        decision = governed_data_access(
            request_id="test-pass-001",
            agent_id="analyst-agent-01",
            action_type=ActionType.DATABASE_QUERY,
            tool="sql_query",
            dataset="sales_metrics",
        )
        assert decision["allowed"] is True
        assert decision["blocked_by"] is None
        assert decision["data_issues"] == []

    def test_pipeline_write_on_clean_table_is_allowed(self):
        decision = governed_data_access(
            request_id="test-pass-002",
            agent_id="pipeline-agent-01",
            action_type=ActionType.DATABASE_WRITE,
            tool="write_db",
            dataset="clean_pipeline_table",
        )
        assert decision["allowed"] is True
        assert decision["blocked_by"] is None

    def test_allowed_decision_includes_quality_metadata(self):
        """
        Even when allowed, the decision should carry quality score and data owner
        so the audit log has full context, not just a pass/fail flag.
        """
        decision = governed_data_access(
            request_id="test-pass-003",
            agent_id="analyst-agent-01",
            action_type=ActionType.DATABASE_QUERY,
            tool="sql_query",
            dataset="sales_metrics",
        )
        assert decision["quality_score"] is not None
        assert decision["data_owner"] is not None


# ---------------------------------------------------------------------------
# Decision shape: contract verification
# ---------------------------------------------------------------------------

class TestDecisionShape:

    def test_every_decision_has_required_fields(self):
        """
        GovernanceDecision TypedDict fields should always be present
        regardless of which layer handled the request.
        """
        required_fields = [
            "request_id", "agent_id", "role", "action", "tool", "dataset",
            "allowed", "blocked_by", "reason", "quality_score",
            "data_owner", "data_issues",
        ]

        scenarios = [
            ("unknown-agent-99", ActionType.DATABASE_QUERY, "sales_metrics"),
            ("analyst-agent-01", ActionType.DATABASE_WRITE, "sales_metrics"),
            ("analyst-agent-01", ActionType.DATABASE_QUERY, "user_events"),
            ("analyst-agent-01", ActionType.DATABASE_QUERY, "sales_metrics"),
        ]

        for i, (agent_id, action_type, dataset) in enumerate(scenarios):
            decision = governed_data_access(
                request_id=f"test-shape-{i:03d}",
                agent_id=agent_id,
                action_type=action_type,
                tool="sql_query",
                dataset=dataset,
            )
            for field in required_fields:
                assert field in decision, (
                    f"Missing field '{field}' in decision for "
                    f"agent={agent_id}, action={action_type}, dataset={dataset}"
                )
