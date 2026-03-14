from typing import List, Dict, Any, Optional
from typing import Optional, List, Dict, Any
"""
Sentry AI — Scenarios Router
Endpoints for triggering pre-defined demo scenarios.
"""

from fastapi import APIRouter, HTTPException

from models.case import CaseRecord
from models.response import BaseResponse
from services.orchestrator import investigate
from models.event import Event, EventType, EventArtifacts, EventContext

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])

# ── Pre-defined scenario events ───────────────────────────────────
SCENARIOS: Dict[str, Event] = {
    "safe-login": Event(
        event_type=EventType.LOGIN,
        user="alice@corp.com",
        source_ip="10.0.0.55",
        device_id="edge-win-3",
        context=EventContext(mfa_used=True, known_device=True),
    ),
    "malicious-login": Event(
        event_type=EventType.LOGIN,
        user="john@corp.com",
        source_ip="185.220.101.1",
        device_id="unknown-device-99",
        context=EventContext(mfa_used=False, known_device=False),
    ),
    "phishing-email": Event(
        event_type=EventType.PHISHING_EMAIL,
        user="ops@corp.com",
        source_ip="0.0.0.0",
        artifacts=EventArtifacts(
            sender="security@c0rp.com",
            subject="Urgent: Verify your account",
            url="https://c0rp-login.evil.com/verify",
            domain="c0rp.com",
        ),
    ),
}


@router.post("/{name}", response_model=BaseResponse[CaseRecord])
async def trigger_scenario(name: str) -> BaseResponse[CaseRecord]:
    """
    Trigger a named demo scenario.
    Accepted names: safe-login, malicious-login, phishing-email
    """
    if name not in SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario '{name}'. "
            f"Available: {', '.join(SCENARIOS.keys())}",
        )

    # Create a fresh event for this scenario run
    event = SCENARIOS[name].model_copy(deep=True)

    # Run through the orchestrator (Stage 3 runs full simulation + saves to DB)
    case = await investigate(event)

    return BaseResponse(
        status="success",
        data=case,
        message=f"Scenario '{name}' completed",
    )
