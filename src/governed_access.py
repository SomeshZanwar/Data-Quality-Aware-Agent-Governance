from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict

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


# ---------------------------------------------------------------------------
# Agent identity registry
# ---------------------------------------------------------------------------

REGISTERED_AGENTS: Dict[str, Dict[str, Any]] = {
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


# ---------------------------------------------------------------------------
# Governance decision type
#
# Using TypedDict makes the contract explicit: callers know exactly what
# fields to expect, and type checkers can catch missing keys at development
# time rather than at runtime.
# ---------------------------------------------------------------------------

class GovernanceDecision(TypedDict):
    request_id: str
    agent_id: str
    role: Optional[str]
    action: str
    tool: str
    dataset: str
    allowed: bool
    blocked_by: Optional[str]       # "identity" | "agent_policy" | "data_quality" | None
    reason: str
    quality_score: Optional[float]
    data_owner: Optional[str]
    data_issues: List[str]


# ---------------------------------------------------------------------------
# Policy engine — created once at module load, shared across all requests.
#
# Previously create_policy_engine() was called inside governed_data_access()
# on every request. That meant a new engine object — with all its rule
# registration — was instantiated per call. For a prototype this is fine,
# but it is the kind of thing that gets flagged in a code review immediately.
# ---------------------------------------------------------------------------

_POLICY_ENGINE = create_policy_engine()


# ---------------------------------------------------------------------------
# Identity verification
# ---------------------------------------------------------------------------

def verify_agent_identity(agent_id: str) -> Dict[str, Any]:
    """
    Check whether the agent is registered before any policy evaluation runs.
    Unknown agents are blocked here — they never reach the policy engine.
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


# ---------------------------------------------------------------------------
# Core governance function
# ---------------------------------------------------------------------------

def governed_data_access(
    request_id: str,
    agent_id: str,
    action_type: ActionType,
    tool: str,
    dataset: str,
) -> GovernanceDecision:
    """
    Three-layer governance check for an agent data access request.

    Layer 0 — Identity:    Is this agent registered?
    Layer 1 — Policy:      Is this agent authorized for this action?
                           (evaluated by Microsoft Agent Governance Toolkit)
    Layer 2 — Data quality: Is the target dataset trustworthy right now?

    The request is allowed only when all three layers pass.
    Each blocked request records which layer stopped it and why.
    """

    # --- Layer 0: Identity ---------------------------------------------------
    identity = verify_agent_identity(agent_id)

    if not identity["verified"]:
        return GovernanceDecision(
            request_id=request_id,
            agent_id=agent_id,
            role=None,
            action=action_type.value,
            tool=tool,
            dataset=dataset,
            allowed=False,
            blocked_by=identity["blocked_by"],
            reason=identity["reason"],
            quality_score=None,
            data_owner=None,
            data_issues=[],
        )

    # --- Layer 1: Agent policy (AGT) -----------------------------------------
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

    policy_allowed, policy_reason = _POLICY_ENGINE.validate_request(request)

    if not policy_allowed:
        return GovernanceDecision(
            request_id=request_id,
            agent_id=agent_id,
            role=identity["role"],
            action=action_type.value,
            tool=tool,
            dataset=dataset,
            allowed=False,
            blocked_by="agent_policy",
            reason=policy_reason,
            quality_score=None,
            data_owner=None,
            data_issues=[],
        )

    # --- Layer 2: Data quality -----------------------------------------------
    quality = check_data_quality(dataset)

    if not quality["trustworthy"]:
        return GovernanceDecision(
            request_id=request_id,
            agent_id=agent_id,
            role=identity["role"],
            action=action_type.value,
            tool=tool,
            dataset=dataset,
            allowed=False,
            blocked_by="data_quality",
            reason=quality["reason"],
            quality_score=quality["quality_score"],
            data_owner=quality["owner"],
            data_issues=quality["issues"],
        )

    # --- All layers passed ---------------------------------------------------
    return GovernanceDecision(
        request_id=request_id,
        agent_id=agent_id,
        role=identity["role"],
        action=action_type.value,
        tool=tool,
        dataset=dataset,
        allowed=True,
        blocked_by=None,
        reason="Agent authorized and dataset passed quality checks.",
        quality_score=quality["quality_score"],
        data_owner=quality["owner"],
        data_issues=[],
    )
