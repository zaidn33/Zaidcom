from typing import List, Dict, Any, Optional
from typing import Optional, List, Dict, Any
"""
Sentry AI — Cases Router
Endpoints for fetching case investigations from the SQLite Audit Store.
"""

from fastapi import APIRouter, HTTPException

from models.case import CaseRecord
from models.response import BaseResponse
from store.audit import list_cases, get_case

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("", response_model=BaseResponse[List[CaseRecord]])
async def get_all_cases() -> BaseResponse[List[CaseRecord]]:
    """List recent investigation cases from the database."""
    cases = await list_cases()
    return BaseResponse(
        status="success",
        data=cases,
        message=f"Retrieved {len(cases)} cases",
    )


@router.get("/{case_id}", response_model=BaseResponse[CaseRecord])
async def get_single_case(case_id: str) -> BaseResponse[CaseRecord]:
    """Fetch a specific case by its SENTRY-XXX ID."""
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return BaseResponse(
        status="success",
        data=case,
        message="Case retrieved successfully",
    )
