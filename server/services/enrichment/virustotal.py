from typing import List, Dict, Any, Optional
from typing import Optional, List, Dict, Any
"""
Sentry AI — VirusTotal Enrichment Provider
Checks IP, domain, and URL reputation via VirusTotal API v3.
Falls back to cached fixtures in DEMO_MODE or on error.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from config import settings
from services.enrichment import BaseProvider, ProviderResult

logger = logging.getLogger("sentry.enrichment.virustotal")

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "virustotal.json"
TIMEOUT = 5.0


class VirusTotalProvider(BaseProvider):
    """VirusTotal IP/domain/URL reputation provider."""

    @property
    def name(self) -> str:
        return "VirusTotal"

    def _load_fixture(self, indicator: str) -> Optional[ProviderResult]:
        """Load cached fixture data for the given indicator."""
        try:
            data: Dict[str, Any] = json.loads(FIXTURE_PATH.read_text())
            if indicator in data:
                entry = data[indicator]
                return ProviderResult(
                    provider=self.name,
                    raw=entry,
                    summary=entry.get("summary", ""),
                    is_cached=True,
                )
        except Exception as exc:
            logger.warning("Failed to load VirusTotal fixture: %s", exc)
        return None

    async def query(self, indicator: str) -> ProviderResult:
        """
        Query VirusTotal for an IP, domain, or URL indicator.
        Returns cached fixture in DEMO_MODE or on API failure.
        """
        # ── Demo mode: always use fixtures ────────────────────────
        if settings.DEMO_MODE:
            fixture = self._load_fixture(indicator)
            if fixture:
                logger.info("[VirusTotal] DEMO_MODE — returning fixture for %s", indicator)
                return fixture
            return ProviderResult(
                provider=self.name,
                summary=f"No fixture data for {indicator}",
                is_cached=True,
            )

        # ── Live API call ─────────────────────────────────────────
        api_key = settings.VIRUSTOTAL_API_KEY
        if not api_key:
            logger.warning("[VirusTotal] No API key — falling back to fixture")
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name, summary="No API key configured"
            )

        # Determine endpoint based on indicator type
        if indicator.startswith("http"):
            # URL lookup requires base64 encoding — simplified for MVP
            endpoint = f"https://www.virustotal.com/api/v3/urls"
        elif "." in indicator and not indicator.replace(".", "").isdigit():
            endpoint = f"https://www.virustotal.com/api/v3/domains/{indicator}"
        else:
            endpoint = f"https://www.virustotal.com/api/v3/ip_addresses/{indicator}"

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    endpoint,
                    headers={"x-apikey": api_key},
                )
                resp.raise_for_status()
                body = resp.json()

                stats = (
                    body.get("data", {})
                    .get("attributes", {})
                    .get("last_analysis_stats", {})
                )
                malicious = stats.get("malicious", 0)
                summary = f"{malicious} vendors flagged as malicious"

                return ProviderResult(
                    provider=self.name,
                    raw=stats,
                    summary=summary,
                    is_cached=False,
                )
        except Exception as exc:
            logger.error("[VirusTotal] API error for %s: %s — falling back to fixture", indicator, exc)
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name,
                summary=f"API error: {exc}",
                is_cached=True,
            )
