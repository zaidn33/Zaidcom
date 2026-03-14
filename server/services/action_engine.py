"""
Sentry AI — Action Engine (Stub)
Will be fully implemented in Stage 3 with reversible demo actions.
"""

from models.action import ActionRequest, ActionResult


async def execute_action(request: ActionRequest) -> ActionResult:
    """
    Execute a safe, reversible demo action.

    Stage 1: returns a placeholder success result.
    Stage 3: will implement block_session, require_mfa,
    quarantine_email, block_url, escalate_to_analyst, allow.
    """
    return ActionResult(
        case_id=request.case_id,
        action_type=request.action_type,
        status="success",
        reason=request.reason,
        reversible=True,
    )


async def rollback_action(action_id: str) -> ActionResult | None:
    """
    Rollback a previously executed action.

    Stage 1: returns None (not implemented).
    Stage 3: will reverse the original action and update audit trail.
    """
    return None
