"""
Sentry AI — Base Enrichment Provider (Abstract Base Class)
All enrichment clients (VirusTotal, AbuseIPDB, IPinfo, vpnapi.io)
must implement this interface to ensure a consistent async contract.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ProviderResult(BaseModel):
    """Standardised result returned by every enrichment provider."""
    provider: str               # e.g. "VirusTotal"
    raw: dict[str, Any] = {}    # Raw API response (or fixture)
    summary: str = ""           # Human-readable one-liner
    is_cached: bool = False     # True if response came from fixture


class BaseProvider(ABC):
    """
    Abstract base class for enrichment providers.

    Every provider must implement:
      - name       → display name for tool-call logs
      - query()    → async enrichment call with fixture fallback

    Subclasses inherit the common timeout / error-handling contract.
    Concrete implementations live in services/enrichment/ (Stage 2).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'VirusTotal')."""
        ...

    @abstractmethod
    async def query(self, indicator: str) -> ProviderResult:
        """
        Query the external API for the given indicator (IP, URL, domain).
        Must handle:
          - Strict timeout (5 s recommended)
          - Fallback to cached fixture on error or in DEMO_MODE
          - Return a ProviderResult with summary and raw payload
        """
        ...
