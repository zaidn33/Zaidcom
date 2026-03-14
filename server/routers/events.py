from typing import List, Dict, Any, Optional
from typing import Optional, List, Dict, Any
"""
Sentry AI — Events Router
Endpoints for ingesting and querying security events.
"""

from fastapi import APIRouter, HTTPException

from models.event import Event
from models.response import BaseResponse
from store.memory import store

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post("", response_model=BaseResponse[Event])
async def ingest_event(event: Event) -> BaseResponse[Event]:
    """Ingest a new security event into the pipeline."""
    stored = store.add_event(event)
    return BaseResponse(status="success", data=stored, message="Event ingested")


@router.get("", response_model=BaseResponse[List[Event]])
async def list_events() -> BaseResponse[List[Event]]:
    """List all ingested events."""
    return BaseResponse(status="success", data=store.list_events())


@router.get("/{event_id}", response_model=BaseResponse[Event])
async def get_event(event_id: str) -> BaseResponse[Event]:
    """Get a single event by ID."""
    event = store.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return BaseResponse(status="success", data=event)
