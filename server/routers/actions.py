"""
Sentry AI — Actions Router
Endpoints for executing and rolling back safe countermeasures.
"""

from fastapi import APIRouter, HTTPException

from models.action import ActionRequest, ActionResult
from models.response import BaseResponse
from services.action_engine import execute_action, rollback_action
from store.memory import store

router = APIRouter(prefix="/api/actions", tags=["Actions"])


@router.post("", response_model=BaseResponse[ActionResult])
async def create_action(request: ActionRequest) -> BaseResponse[ActionResult]:
    """Execute a safe, reversible demo action on a case."""
    result = await execute_action(request)
    store.add_action(result)
    return BaseResponse(
        status="success",
        data=result,
        message=f"Action '{result.action_type}' executed",
    )


@router.post("/{action_id}/rollback", response_model=BaseResponse[ActionResult])
async def rollback(action_id: str) -> BaseResponse[ActionResult]:
    """Rollback a previously executed action."""
    existing = store.get_action(action_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Action not found")

    rolled_back = await rollback_action(action_id)
    if not rolled_back:
        raise HTTPException(status_code=400, detail="Rollback not implemented yet")

    return BaseResponse(
        status="success",
        data=rolled_back,
        message="Action rolled back",
    )


@router.get("", response_model=BaseResponse[list[ActionResult]])
async def list_actions() -> BaseResponse[list[ActionResult]]:
    """List all executed actions."""
    return BaseResponse(status="success", data=store.list_actions())
