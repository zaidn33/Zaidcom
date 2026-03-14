"""
Sentry AI — Action Schemas (Pydantic v2)
Defines the request/result models for reversible demo actions.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


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
    """Result of an executed (or rolled-back) action."""
    model_config = ConfigDict(from_attributes=True)

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    action_type: ActionType
    status: str = "success"         # "success" | "failed" | "rolled_back"
    reason: str = ""
    reversible: bool = True
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
