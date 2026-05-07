from datetime import datetime
from typing import Dict, Any

from agent_os import PolicyEngine
from agent_control_plane.agent_kernel import (
    AgentContext,
    ActionType,
    ExecutionRequest,
    PermissionLevel,
    PolicyRule,
)


def block_analyst_database_write(request: ExecutionRequest) -> bool:
    """
    Analysts can query data, but they cannot write to databases.
    Return True when allowed.
    Return False when blocked.
    """
    role = request.agent_context.metadata.get("role")

    if role == "analyst" and request.action_type == ActionType.DATABASE_WRITE:
        return False

    return True


def create_policy_engine() -> PolicyEngine:
    """
    Create the AGT policy engine and register project-specific governance rules.
    """
    engine = PolicyEngine()

    engine.add_custom_rule(
        PolicyRule(
            rule_id="block-analyst-database-write",
            name="Block analyst database writes",
            description="Analyst agents can query data, but cannot write to databases.",
            action_types=[ActionType.DATABASE_WRITE],
            validator=block_analyst_database_write,
            priority=100,
        )
    )

    return engine


def create_agent_context(
    agent_id: str,
    role: str,
    permissions: Dict[ActionType, PermissionLevel],
    metadata: Dict[str, Any] | None = None,
) -> AgentContext:
    """
    Create an AGT AgentContext object for a governed agent.
    """
    merged_metadata = metadata or {}
    merged_metadata["role"] = role

    return AgentContext(
        agent_id=agent_id,
        session_id=f"session-{agent_id}",
        created_at=datetime.now(),
        permissions=permissions,
        metadata=merged_metadata,
    )


def create_execution_request(
    request_id: str,
    agent_context: AgentContext,
    action_type: ActionType,
    tool: str,
    dataset: str,
) -> ExecutionRequest:
    """
    Create an AGT ExecutionRequest for a specific agent action.
    """
    return ExecutionRequest(
        request_id=request_id,
        agent_context=agent_context,
        action_type=action_type,
        parameters={
            "tool": tool,
            "dataset": dataset,
        },
        timestamp=datetime.now(),
    )