"""
Sentry AI — Case Record & Tool Call Schemas (Pydantic v2)
Tracks investigation results and the agent's tool-use trajectory.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


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
    The complete investigation record for a single event.
    Contains risk score, signals, full tool trajectory, and action taken.
    """
    model_config = ConfigDict(from_attributes=True)

    case_id: str = Field(default_factory=lambda: str(uuid4()))
    event_id: str
    risk_score: int = 0             # 0-100
    classification: RiskClassification = RiskClassification.LOW
    signals: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    action: str = ""                # e.g. "block_session"
    action_status: str = ""         # "success" | "failed" | "pending"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
