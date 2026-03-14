"""
Sentry AI — Case Record & Tool Call Schemas (Pydantic v2)
Tracks investigation results and the agent's tool-use trajectory.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


def generate_case_id() -> str:
    """Generate a unique 8-character hex ID prefixed with SENTRY-"""
    return f"SENTRY-{uuid.uuid4().hex[:8].upper()}"


def generate_timestamp() -> str:
    """Generate a UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


class RiskClassification(str, Enum):
    """Risk classification levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolCall(BaseModel):
    """
    A single tool invocation record in the agent trajectory.
    Captures what was called, the outcome, and timing.
    """
    model_config = ConfigDict(from_attributes=True)

    tool: str                       # e.g. "VirusTotal"
    status: str                     # "ok" | "error" | "cached"
    latency_ms: float = 0.0
    summary: str                    # e.g. "12 vendors flagged IP"


class CaseRecord(BaseModel):
    """
    The core record of an investigation.
    Ties together the event, the agent's findings, scoring, and action taken.
    """
    model_config = ConfigDict(from_attributes=True)

    case_id: str = Field(default_factory=generate_case_id)
    event_id: str
    risk_score: int                 # 0-100
    classification: RiskClassification
    reasoning: str = ""
    signals: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    action: str                     # e.g. "block_session"
    action_status: str              # "success" | "failed" | "pending"
    created_at: str = Field(default_factory=generate_timestamp)
    updated_at: str | None = None
