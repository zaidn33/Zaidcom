"""
Sentry AI — Orchestrator Service
Runs the full investigation pipeline: enrichment → signal detection → scoring.
Exposes the agent trajectory as a list of ToolCall entries for the UI.
"""

import asyncio
import logging
import time

from models.event import Event, EventType
from models.case import CaseRecord, ToolCall, RiskClassification
from services.enrichment import ProviderResult
from services.enrichment.virustotal import VirusTotalProvider
from services.enrichment.abuseipdb import AbuseIPDBProvider
from services.enrichment.ipinfo import IPinfoProvider
from services.enrichment.vpnapi import VPNAPIProvider
from services.scoring import compute_risk, ScoringResult
from store.context import KNOWN_DEVICES, RECENT_LOGINS, TRUSTED_IPS, SAFE_DOMAINS

logger = logging.getLogger("sentry.orchestrator")

# ── Provider Singletons ──────────────────────────────────────────
_vt = VirusTotalProvider()
_abuse = AbuseIPDBProvider()
_ipinfo = IPinfoProvider()
_vpnapi = VPNAPIProvider()


async def _timed_query(provider, indicator: str) -> tuple[ProviderResult, ToolCall]:
    """Run a provider query and wrap the result with timing metadata."""
    start = time.perf_counter()
    try:
        result = await provider.query(indicator)
        elapsed = (time.perf_counter() - start) * 1000
        tool_call = ToolCall(
            tool=provider.name,
            status="cached" if result.is_cached else "ok",
            latency_ms=round(elapsed, 1),
            summary=result.summary,
        )
        return result, tool_call
    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        tool_call = ToolCall(
            tool=provider.name,
            status="error",
            latency_ms=round(elapsed, 1),
            summary=f"Error: {exc}",
        )
        return ProviderResult(provider=provider.name, summary=f"Error: {exc}"), tool_call


def _detect_impossible_travel(
    user: str, current_location: str
) -> tuple[bool, str]:
    """
    Compare the current login geolocation against the user's most
    recent login location from the internal context store.

    Returns (is_impossible, detail_string).
    """
    recent = RECENT_LOGINS.get(user, [])
    if not recent:
        return False, ""

    last_login = recent[0]  # most recent entry
    last_location = last_login.get("location", "")

    if not last_location or not current_location:
        return False, ""

    # Normalise for comparison (case-insensitive, stripped)
    last_norm = last_location.strip().lower()
    curr_norm = current_location.strip().lower()

    if last_norm != curr_norm:
        detail = f"from {last_location} to {current_location}"
        return True, detail

    return False, ""


async def investigate(event: Event) -> CaseRecord:
    """
    Full investigation pipeline.

    Steps:
      1. Receive event
      2. Classify event type
      3. Select enrichment providers for event type
      4. Call providers in parallel
      5. Query internal context store
      6. Detect signals from enrichment + context
      7. Compute risk score + reasoning
      8. Return populated CaseRecord (action deferred to Stage 3)
    """
    tool_calls: list[ToolCall] = []
    signals: list[str] = []
    context_details: dict[str, str] = {}

    # ── Step 1-2: Classify ────────────────────────────────────────
    logger.info("[Orchestrator] Investigating event %s (type=%s, user=%s)",
                event.event_id, event.event_type.value, event.user)

    # ── Step 3-4: Enrichment based on event type ──────────────────
    if event.event_type == EventType.LOGIN:
        # Login: query all 4 providers on source_ip
        results = await asyncio.gather(
            _timed_query(_vt, event.source_ip),
            _timed_query(_abuse, event.source_ip),
            _timed_query(_ipinfo, event.source_ip),
            _timed_query(_vpnapi, event.source_ip),
        )
        vt_result, vt_tc = results[0]
        abuse_result, abuse_tc = results[1]
        ipinfo_result, ipinfo_tc = results[2]
        vpn_result, vpn_tc = results[3]
        tool_calls.extend([vt_tc, abuse_tc, ipinfo_tc, vpn_tc])

        # ── Step 5-6: Signal detection for logins ─────────────────

        # Malicious IP: VirusTotal ≥3 malicious OR AbuseIPDB confidence ≥50
        vt_malicious = vt_result.raw.get("malicious", 0)
        abuse_confidence = abuse_result.raw.get("abuse_confidence_score", 0)
        if vt_malicious >= 3 or abuse_confidence >= 50:
            signals.append("malicious_ip")
            context_details["malicious_ip"] = (
                f"VirusTotal: {vt_malicious} vendors flagged; "
                f"AbuseIPDB: {abuse_confidence}% confidence"
            )

        # VPN/Proxy/Tor
        vpn_flag = vpn_result.raw.get("vpn", False)
        proxy_flag = vpn_result.raw.get("proxy", False)
        tor_flag = vpn_result.raw.get("tor", False)
        if vpn_flag or proxy_flag or tor_flag:
            signals.append("vpn_detected")
            active = [n for n, v in [("VPN", vpn_flag), ("proxy", proxy_flag), ("Tor", tor_flag)] if v]
            context_details["vpn_detected"] = " + ".join(active) + " active"

        # Impossible Travel: compare current geo vs last known location
        current_city = ipinfo_result.raw.get("city", "")
        current_country = ipinfo_result.raw.get("country", "")
        current_location = f"{current_city}, {current_country}" if current_city else ""
        is_travel, travel_detail = _detect_impossible_travel(event.user, current_location)
        if is_travel:
            signals.append("impossible_travel")
            context_details["impossible_travel"] = travel_detail

        # Unknown Device
        user_devices = KNOWN_DEVICES.get(event.user, [])
        if event.device_id and event.device_id not in user_devices:
            signals.append("unknown_device")
            context_details["unknown_device"] = (
                f"device '{event.device_id}' not in known list: {user_devices}"
            )

        # Safe Allowlist
        if event.source_ip in TRUSTED_IPS:
            signals.append("safe_allowlist")
            context_details["safe_allowlist"] = f"IP {event.source_ip} is in trusted allowlist"

    elif event.event_type == EventType.PHISHING_EMAIL:
        # Phishing: query VirusTotal on domain AND URL
        queries = []
        if event.artifacts.domain:
            queries.append(_timed_query(_vt, event.artifacts.domain))
        if event.artifacts.url:
            queries.append(_timed_query(_vt, event.artifacts.url))

        results = await asyncio.gather(*queries)
        for result, tc in results:
            tool_calls.append(tc)

        # Detect signals from phishing enrichment
        for result, tc in results:
            malicious = result.raw.get("malicious", 0)
            if malicious >= 3:
                if "malicious_ip" not in signals:
                    signals.append("malicious_ip")
                    context_details["malicious_ip"] = (
                        f"{tc.tool} flagged indicator: {malicious} vendors"
                    )
                # High-confidence phishing: if multiple indicators agree or
                # vendor count is high, add the phishing-specific signal
                if malicious >= 5 and "high_confidence_phish" not in signals:
                    signals.append("high_confidence_phish")
                    context_details["high_confidence_phish"] = (
                        f"{malicious} vendors confirmed phishing indicator"
                    )

        # Check if sender domain is safe (reduce false positive)
        sender_domain = event.artifacts.sender.split("@")[-1] if event.artifacts.sender else ""
        if sender_domain in SAFE_DOMAINS:
            signals.append("safe_allowlist")
            context_details["safe_allowlist"] = f"Sender domain '{sender_domain}' is trusted"

    elif event.event_type == EventType.URL_CLICK:
        # URL Click: query VirusTotal on the URL
        if event.artifacts.url:
            vt_result, vt_tc = await _timed_query(_vt, event.artifacts.url)
            tool_calls.append(vt_tc)

            malicious = vt_result.raw.get("malicious", 0)
            if malicious >= 3:
                signals.append("malicious_ip")
                context_details["malicious_ip"] = (
                    f"VirusTotal flagged URL: {malicious} vendors"
                )
            if malicious >= 5:
                signals.append("high_confidence_phish")
                context_details["high_confidence_phish"] = (
                    f"{malicious} vendors confirmed malicious URL"
                )

    # ── Step 7: Score ─────────────────────────────────────────────
    scoring: ScoringResult = compute_risk(signals, context_details)

    logger.info(
        "[Orchestrator] Event %s → score=%d, classification=%s, signals=%s",
        event.event_id, scoring.score, scoring.classification.value, signals,
    )

    # ── Step 8: Build CaseRecord (action deferred to Stage 3) ────
    return CaseRecord(
        event_id=event.event_id,
        risk_score=scoring.score,
        classification=scoring.classification,
        signals=scoring.signals,
        tool_calls=tool_calls,
        action="",
        action_status="pending",
    )
