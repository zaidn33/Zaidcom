"""
Sentry AI — AbuseIPDB Enrichment Provider
Checks IP abuse confidence score via AbuseIPDB API v2.
Falls back to cached fixtures in DEMO_MODE or on error.
"""

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from config import settings
from services.enrichment import BaseProvider, ProviderResult

logger = logging.getLogger("sentry.enrichment.abuseipdb")

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "abuseipdb.json"
TIMEOUT = 5.0


class AbuseIPDBProvider(BaseProvider):
    """AbuseIPDB IP abuse confidence provider."""

    @property
    def name(self) -> str:
        return "AbuseIPDB"

    def _load_fixture(self, indicator: str) -> ProviderResult | None:
        """Load cached fixture data for the given IP."""
        try:
            data: dict[str, Any] = json.loads(FIXTURE_PATH.read_text())
            if indicator in data:
                entry = data[indicator]
                return ProviderResult(
                    provider=self.name,
                    raw=entry,
                    summary=entry.get("summary", ""),
                    is_cached=True,
                )
        except Exception as exc:
            logger.warning("Failed to load AbuseIPDB fixture: %s", exc)
        return None

    async def query(self, indicator: str) -> ProviderResult:
        """
        Query AbuseIPDB for an IP address.
        Returns cached fixture in DEMO_MODE or on API failure.
        """
        if settings.DEMO_MODE:
            fixture = self._load_fixture(indicator)
            if fixture:
                logger.info("[AbuseIPDB] DEMO_MODE — returning fixture for %s", indicator)
                return fixture
            return ProviderResult(
                provider=self.name,
                summary=f"No fixture data for {indicator}",
                is_cached=True,
            )

        api_key = settings.ABUSEIPDB_API_KEY
        if not api_key:
            logger.warning("[AbuseIPDB] No API key — falling back to fixture")
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name, summary="No API key configured"
            )

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": indicator, "maxAgeInDays": 90},
                    headers={"Key": api_key, "Accept": "application/json"},
                )
                resp.raise_for_status()
                body = resp.json().get("data", {})

                confidence = body.get("abuseConfidenceScore", 0)
                reports = body.get("totalReports", 0)
                summary = f"{confidence}% abuse confidence — {reports} reports"

                return ProviderResult(
                    provider=self.name,
                    raw=body,
                    summary=summary,
                    is_cached=False,
                )
        except Exception as exc:
            logger.error("[AbuseIPDB] API error for %s: %s — falling back to fixture", indicator, exc)
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name,
                summary=f"API error: {exc}",
                is_cached=True,
            )
