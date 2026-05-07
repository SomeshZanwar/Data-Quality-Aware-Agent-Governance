from typing import Dict, Any

from agent_control_plane.agent_kernel import (
    ActionType,
    PermissionLevel,
)

from agent_policy import (
    create_policy_engine,
    create_agent_context,
    create_execution_request,
)
from data_quality_registry import check_data_quality


REGISTERED_AGENTS = {
    "analyst-agent-01": {
        "role": "analyst",
        "permissions": {
            ActionType.DATABASE_QUERY: PermissionLevel.READ_ONLY,
            ActionType.FILE_READ: PermissionLevel.READ_ONLY,
            ActionType.DATABASE_WRITE: PermissionLevel.NONE,
        },
    },
    "pipeline-agent-01": {
        "role": "pipeline",
        "permissions": {
            ActionType.DATABASE_QUERY: PermissionLevel.READ_ONLY,
            ActionType.FILE_READ: PermissionLevel.READ_ONLY,
            ActionType.DATABASE_WRITE: PermissionLevel.READ_WRITE,
        },
    },
}


def verify_agent_identity(agent_id: str) -> Dict[str, Any]:
    """
    Verify whether the agent is registered before policy evaluation.
    Unknown agents are blocked immediately.
    """
    agent = REGISTERED_AGENTS.get(agent_id)

    if not agent:
        return {
            "verified": False,
            "blocked_by": "identity",
            "reason": f"Agent '{agent_id}' is not registered.",
        }

    return {
        "verified": True,
        "role": agent["role"],
        "permissions": agent["permissions"],
    }


def governed_data_access(
    request_id: str,
    agent_id: str,
    action_type: ActionType,
    tool: str,
    dataset: str,
) -> Dict[str, Any]:
    """
    Two-layer governance check.

    Layer 0: Agent identity
    Layer 1: Agent authorization using Microsoft Agent Governance Toolkit
    Layer 2: Dataset trustworthiness using data quality validation

    Final decision is allowed only when all checks pass.
    """
    identity = verify_agent_identity(agent_id)

    if not identity["verified"]:
        return {
            "request_id": request_id,
            "agent_id": agent_id,
            "role": None,
            "action": action_type.value,
            "tool": tool,
            "dataset": dataset,
            "allowed": False,
            "blocked_by": identity["blocked_by"],
            "reason": identity["reason"],
            "quality_score": None,
            "data_owner": None,
            "data_issues": [],
        }

    engine = create_policy_engine()

    agent_context = create_agent_context(
        agent_id=agent_id,
        role=identity["role"],
        permissions=identity["permissions"],
    )

    request = create_execution_request(
        request_id=request_id,
        agent_context=agent_context,
        action_type=action_type,
        tool=tool,
        dataset=dataset,
    )

    policy_allowed, policy_reason = engine.validate_request(request)

    if not policy_allowed:
        return {
            "request_id": request_id,
            "agent_id": agent_id,
            "role": identity["role"],
            "action": action_type.value,
            "tool": tool,
            "dataset": dataset,
            "allowed": False,
            "blocked_by": "agent_policy",
            "reason": policy_reason,
            "quality_score": None,
            "data_owner": None,
            "data_issues": [],
        }

    quality = check_data_quality(dataset)

    if not quality["trustworthy"]:
        return {
            "request_id": request_id,
            "agent_id": agent_id,
            "role": identity["role"],
            "action": action_type.value,
            "tool": tool,
            "dataset": dataset,
            "allowed": False,
            "blocked_by": "data_quality",
            "reason": quality["reason"],
            "quality_score": quality["quality_score"],
            "data_owner": quality["owner"],
            "data_issues": quality["issues"],
        }

    return {
        "request_id": request_id,
        "agent_id": agent_id,
        "role": identity["role"],
        "action": action_type.value,
        "tool": tool,
        "dataset": dataset,
        "allowed": True,
        "blocked_by": None,
        "reason": "Agent authorized and dataset passed quality checks.",
        "quality_score": quality["quality_score"],
        "data_owner": quality["owner"],
        "data_issues": [],
    }