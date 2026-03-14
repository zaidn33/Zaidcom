"""
Sentry AI — vpnapi.io Enrichment Provider
Detects VPN, proxy, and Tor usage for an IP address.
Falls back to cached fixtures in DEMO_MODE or on error.
"""

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from config import settings
from services.enrichment import BaseProvider, ProviderResult

logger = logging.getLogger("sentry.enrichment.vpnapi")

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "vpnapi.json"
TIMEOUT = 5.0


class VPNAPIProvider(BaseProvider):
    """vpnapi.io VPN/proxy/Tor detection provider."""

    @property
    def name(self) -> str:
        return "vpnapi.io"

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
            logger.warning("Failed to load vpnapi fixture: %s", exc)
        return None

    async def query(self, indicator: str) -> ProviderResult:
        """
        Query vpnapi.io for VPN/proxy/Tor detection on an IP.
        Returns cached fixture in DEMO_MODE or on API failure.
        """
        if settings.DEMO_MODE:
            fixture = self._load_fixture(indicator)
            if fixture:
                logger.info("[vpnapi.io] DEMO_MODE — returning fixture for %s", indicator)
                return fixture
            return ProviderResult(
                provider=self.name,
                summary=f"No fixture data for {indicator}",
                is_cached=True,
            )

        api_key = settings.VPNAPI_API_KEY
        if not api_key:
            logger.warning("[vpnapi.io] No API key — falling back to fixture")
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name, summary="No API key configured"
            )

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    f"https://vpnapi.io/api/{indicator}",
                    params={"key": api_key},
                )
                resp.raise_for_status()
                body = resp.json()

                sec = body.get("security", {})
                vpn = sec.get("vpn", False)
                proxy = sec.get("proxy", False)
                tor = sec.get("tor", False)

                parts = []
                if vpn:
                    parts.append("VPN")
                if proxy:
                    parts.append("proxy")
                if tor:
                    parts.append("Tor")
                summary = " + ".join(parts) + " detected" if parts else "No VPN/proxy/Tor detected"

                return ProviderResult(
                    provider=self.name,
                    raw={"vpn": vpn, "proxy": proxy, "tor": tor, "relay": sec.get("relay", False)},
                    summary=summary,
                    is_cached=False,
                )
        except Exception as exc:
            logger.error("[vpnapi.io] API error for %s: %s — falling back to fixture", indicator, exc)
            return self._load_fixture(indicator) or ProviderResult(
                provider=self.name,
                summary=f"API error: {exc}",
                is_cached=True,
            )
