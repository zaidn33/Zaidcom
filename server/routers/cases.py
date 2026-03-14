"""
Sentry AI — Cases Router
Endpoints for querying investigation case records.
"""

from fastapi import APIRouter, HTTPException

from models.case import CaseRecord
from models.response import BaseResponse
from store.memory import store

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("", response_model=BaseResponse[list[CaseRecord]])
async def list_cases() -> BaseResponse[list[CaseRecord]]:
    """List all case records."""
    return BaseResponse(status="success", data=store.list_cases())


@router.get("/{case_id}", response_model=BaseResponse[CaseRecord])
async def get_case(case_id: str) -> BaseResponse[CaseRecord]:
    """Get a single case record by ID."""
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return BaseResponse(status="success", data=case)
