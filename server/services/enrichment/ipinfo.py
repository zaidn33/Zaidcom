"""
Sentry AI — IPinfo Enrichment Provider
Provides IP geolocation and ASN data via IPinfo API.
Falls back to cached fixtures in DEMO_MODE or on error.
"""

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from config import settings
from services.enrichment import BaseProvider, ProviderResult

logger = logging.getLogger("sentry.enrichment.ipinfo")

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "ipinfo.json"
TIMEOUT = 5.0


class IPinfoProvider(BaseProvider):
    """IPinfo geolocation and ASN provider."""

    @property
    def name(self) -> str:
        return "IPinfo"

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
            logger.warning("Failed to load IPinfo fixture: %s", exc)
        return None

    async def query(self, indicator: str) -> ProviderResult:
        """
        Query IPinfo for geolocation of an IP address.
        Returns cached fixture in DEMO_MODE or on API failure.
        """
        if settings.DEMO_MODE:
            fixture = self._load_fixture(indicator)
            if fixture:
                logger.info("[IPinfo] DEMO_MODE — returning fixture for %s", indicator)
                return fixture
            return ProviderResult(
                provider=self.name,
                summary=f"No fixture data for {indicator}",
                is_cached=True,
            )

        api_key = settings.IPINFO_API_KEY
        if not api_key:
            logger.warning("[IPinfo] No API key — falling back to fixture")
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name, summary="No API key configured"
            )

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    f"https://ipinfo.io/{indicator}/json",
                    params={"token": api_key},
                )
                resp.raise_for_status()
                body = resp.json()

                city = body.get("city", "Unknown")
                country = body.get("country", "??")
                org = body.get("org", "Unknown")
                summary = f"{city}, {country} — {org}"

                return ProviderResult(
                    provider=self.name,
                    raw=body,
                    summary=summary,
                    is_cached=False,
                )
        except Exception as exc:
            logger.error("[IPinfo] API error for %s: %s — falling back to fixture", indicator, exc)
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name,
                summary=f"API error: {exc}",
                is_cached=True,
            )
