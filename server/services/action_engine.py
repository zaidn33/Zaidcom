"""
Sentry AI — Action Engine
Executes reversible demo countermeasures and handles rollbacks.
"""

import logging
from models.action import ActionRequest, ActionResult, ActionType

logger = logging.getLogger("sentry.action_engine")


async def execute_action(request: ActionRequest) -> ActionResult:
    """
    Execute a safe, reversible demo action based on type.
    """
    logger.info("Executing action '%s' for case '%s'", request.action_type.value, request.case_id)
    
    # In a real app, this would call Azure AD, Okta, crowdstrike, etc.
    # For MVP, we simulate success for all 5 demo actions.
    
    if request.action_type == ActionType.ALLOW:
        status_msg = "Skipped - no action required"
    elif request.action_type == ActionType.BLOCK_SESSION:
        status_msg = "User session terminated and token revoked"
    elif request.action_type == ActionType.REQUIRE_MFA:
        status_msg = "MFA prompt triggered for next login"
    elif request.action_type == ActionType.QUARANTINE_EMAIL:
        status_msg = "Email moved to admin quarantine"
    elif request.action_type == ActionType.BLOCK_URL:
        status_msg = "URL added to SWG blocklist"
    else:
        status_msg = "Unknown action type executed"

    # escalate_to_analyst is handled by orchestrator setting action="escalated"
    # and avoiding this engine entirely.

    return ActionResult(
        case_id=request.case_id,
        action_type=request.action_type,
        status="success",
        reason=f"{status_msg} ({request.reason})",
        reversible=request.action_type != ActionType.ALLOW,
    )


async def rollback_action(action: ActionResult) -> ActionResult:
    """
    Rollback a previously executed action.
    """
    if not action.reversible:
        return action

    logger.info("Rolling back action '%s' for case '%s'", action.action_id, action.case_id)
    
    # Simulate API call to reverse action
    action.status = "rolled_back"
    action.reason = f"[Rolled back] {action.reason}"
    
    return action
