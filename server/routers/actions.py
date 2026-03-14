"""
Sentry AI — Actions Router
Endpoints for executing and rolling back countermeasures.
"""

from fastapi import APIRouter, HTTPException

from models.action import ActionRequest, ActionResult
from models.response import BaseResponse
from services.action_engine import execute_action, rollback_action
from store.audit import save_action, get_action_for_case

router = APIRouter(prefix="/api/actions", tags=["Actions"])


@router.post("", response_model=BaseResponse[ActionResult])
async def execute(request: ActionRequest) -> BaseResponse[ActionResult]:
    """Execute a countermeasure for a case."""
    result = await execute_action(request)
    await save_action(result)
    
    return BaseResponse(
        status="success",
        data=result,
        message=f"Action '{request.action_type.value}' executed successfully",
    )


@router.post("/{action_id}/rollback", response_model=BaseResponse[ActionResult])
async def rollback(action_id: str) -> BaseResponse[ActionResult]:
    """Rollback a previously executed action."""
    import aiosqlite
    from store.audit import DATABASE_URL, save_action
    from models.action import ActionType

    # 1. Fetch action from DB directly
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Action not found")
            
            action = ActionResult(
                action_id=row["action_id"],
                case_id=row["case_id"],
                action_type=ActionType(row["action_type"]),
                status=row["status"],
                reason=row["reason"],
                reversible=row["reversible"],
                executed_at=row["executed_at"]
            )

    # 2. Check if already rolled back
    if action.status == "rolled_back":
        raise HTTPException(status_code=400, detail="Action is already rolled back")

    # 3. Roll it back
    rolled_back_action = await rollback_action(action)
    
    # 4. Save updated status
    await save_action(rolled_back_action)

    # 5. We should also update the case action_status to rolled_back
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("UPDATE cases SET action_status = 'rolled_back' WHERE case_id = ?", (action.case_id,))
        await db.commit()

    return BaseResponse(
        status="success",
        data=rolled_back_action,
        message=f"Action '{action.action_id}' rolled back successfully",
    )
