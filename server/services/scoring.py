"""
Sentry AI — Weighted Risk Scoring Engine
Deterministic signal-based scoring with human-readable reasoning summary.

Signal weights (from PRD):
  malicious_ip           +35
  vpn_detected           +15
  impossible_travel      +25
  unknown_device         +10
  failed_auth_spike      +10
  high_confidence_phish  +15   (phishing-specific enrichment signal)
  safe_allowlist         -25

Classification thresholds:
  0–39  → LOW
  40–69 → MEDIUM
  70+   → HIGH

Score is clamped to [0, 100].
"""

from dataclasses import dataclass

from models.case import RiskClassification


# ── Weight Table ──────────────────────────────────────────────────
SIGNAL_WEIGHTS: dict[str, int] = {
    "malicious_ip": 35,
    "vpn_detected": 15,
    "impossible_travel": 25,
    "unknown_device": 10,
    "failed_auth_spike": 10,
    "high_confidence_phish": 15,
    "safe_allowlist": -25,
}

# Human-readable descriptions for the reasoning summary
SIGNAL_DESCRIPTIONS: dict[str, str] = {
    "malicious_ip": "IP flagged as malicious by threat intelligence",
    "vpn_detected": "active VPN or proxy usage detected",
    "impossible_travel": "impossible travel detected between login locations",
    "unknown_device": "login from an unrecognised device",
    "failed_auth_spike": "spike in failed authentication attempts",
    "high_confidence_phish": "high-confidence phishing indicators in email/URL",
    "safe_allowlist": "source matched trusted allowlist (risk reduced)",
}


@dataclass
class ScoringResult:
    """Complete scoring output with score, classification, and reasoning."""
    score: int
    classification: RiskClassification
    signals: list[str]
    reasoning: str


def compute_risk(
    signals: list[str],
    context_details: dict[str, str] | None = None,
) -> ScoringResult:
    """
    Compute a deterministic risk score from detected signals.

    Args:
        signals: List of signal keys (e.g. ["malicious_ip", "vpn_detected"]).
        context_details: Optional dict mapping signal keys to specific context
                         strings for richer reasoning (e.g. impossible_travel →
                         "from Toronto, CA to Moscow, RU").

    Returns:
        ScoringResult with score, classification, signals, and reasoning string.
    """
    context_details = context_details or {}
    raw_score = 0
    reasoning_parts: list[str] = []

    for signal in signals:
        weight = SIGNAL_WEIGHTS.get(signal, 0)
        raw_score += weight

        # Build reasoning line with optional context
        base_desc = SIGNAL_DESCRIPTIONS.get(signal, signal)
        detail = context_details.get(signal)
        if detail:
            reasoning_parts.append(f"{base_desc} ({detail})")
        else:
            reasoning_parts.append(base_desc)

    # Clamp to [0, 100]
    clamped = max(0, min(100, raw_score))

    # Classify
    if clamped >= 70:
        classification = RiskClassification.HIGH
    elif clamped >= 40:
        classification = RiskClassification.MEDIUM
    else:
        classification = RiskClassification.LOW

    # Assemble reasoning string
    if not reasoning_parts:
        reasoning = "No risk signals detected — event appears safe."
    else:
        level = classification.value.upper()
        summary_list = "; ".join(reasoning_parts)
        reasoning = f"{level} risk due to: {summary_list}."

    return ScoringResult(
        score=clamped,
        classification=classification,
        signals=signals,
        reasoning=reasoning,
    )
