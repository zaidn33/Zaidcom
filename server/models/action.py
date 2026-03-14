"""
Sentry AI — Action Schemas (Pydantic v2)
Defines the request/result models for reversible demo actions.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


def generate_action_id() -> str:
    """Generate a unique 8-character hex ID prefixed with ACT-"""
    return f"ACT-{uuid.uuid4().hex[:8].upper()}"


def generate_timestamp() -> str:
    """Generate an ISO-formatted timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


class ActionType(str, Enum):
    """Allowed reversible demo action types."""
    BLOCK_SESSION = "block_session"
    REQUIRE_MFA = "require_mfa"
    QUARANTINE_EMAIL = "quarantine_email"
    BLOCK_URL = "block_url"
    ESCALATE_TO_ANALYST = "escalate_to_analyst"
    ALLOW = "allow"


class ActionRequest(BaseModel):
    """Inbound request to execute an action on a case."""
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    action_type: ActionType
    reason: str = ""


class ActionResult(BaseModel):
    """
    The result of executing a countermeasure.
    Used for audit logging and the UI dashboard.
    """
    model_config = ConfigDict(from_attributes=True)

    action_id: str = Field(default_factory=generate_action_id)
    case_id: str
    action_type: ActionType
    status: str = "success"         # "success" | "failed" | "rolled_back"
    reason: str = ""
    reversible: bool = True
    executed_at: str = Field(default_factory=generate_timestamp)
