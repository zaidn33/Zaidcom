"""
Sentry AI — Common Event Schema (Pydantic v2)
Maps all incoming security events to a normalized format.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Supported security event types."""
    LOGIN = "login"
    PHISHING_EMAIL = "phishing_email"
    URL_CLICK = "url_click"


class EventArtifacts(BaseModel):
    """Artifacts attached to the event (URLs, domains, email metadata)."""
    model_config = ConfigDict(from_attributes=True)

    url: str = ""
    domain: str = ""
    sender: str = ""
    subject: str = ""


class EventContext(BaseModel):
    """Contextual flags for the event."""
    model_config = ConfigDict(from_attributes=True)

    mfa_used: bool = False
    known_device: bool = False


class Event(BaseModel):
    """
    Common event schema — the single normalized format for all
    ingested security events (login, phishing, URL click).
    """
    model_config = ConfigDict(from_attributes=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    user: str                       # e.g. "john@corp.com"
    source_ip: str                  # e.g. "185.220.101.1"
    device_id: str = ""             # e.g. "chrome-win-1"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    artifacts: EventArtifacts = Field(default_factory=EventArtifacts)
    context: EventContext = Field(default_factory=EventContext)
