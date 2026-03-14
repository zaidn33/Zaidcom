from typing import List, Dict, Any, Optional
from typing import Optional, List, Dict, Any
"""
Sentry AI — Internal Context Store
Pre-seeded data simulating organisational knowledge:
known devices, recent login history, trusted IPs, and safe domains.

This data is used by the orchestrator during enrichment (Stage 2+).
"""

# ── Known Devices (user → list of device fingerprints) ────────────
KNOWN_DEVICES: Dict[str, List[str]] = {
    "john@corp.com": ["chrome-win-1", "firefox-mac-2"],
    "alice@corp.com": ["edge-win-3"],
    "ops@corp.com": ["chrome-linux-4"],
    "mike@corp.com": ["safari-mac-5", "chrome-win-6"],
}

# ── Executives (High-Risk Targets) ─────────────────────────────────
EXECUTIVES: set[str] = {
    "alice@corp.com",
    "ceo@corp.com",
}

# ── Recent Login History (user → list of login records) ───────────
RECENT_LOGINS: Dict[str, List[dict]] = {
    "john@corp.com": [
        {"ip": "10.0.0.50", "location": "Toronto, CA", "time": "2026-03-14T01:00:00Z", "device": "chrome-win-1"},
        {"ip": "10.0.0.50", "location": "Toronto, CA", "time": "2026-03-13T18:30:00Z", "device": "chrome-win-1"},
    ],
    "alice@corp.com": [
        {"ip": "10.0.0.55", "location": "Toronto, CA", "time": "2026-03-14T02:15:00Z", "device": "edge-win-3"},
    ],
    "ops@corp.com": [
        {"ip": "10.0.0.60", "location": "Toronto, CA", "time": "2026-03-14T02:10:00Z", "device": "chrome-linux-4"},
    ],
    "mike@corp.com": [
        {"ip": "10.0.0.70", "location": "Toronto, CA", "time": "2026-03-14T02:20:00Z", "device": "safari-mac-5"},
    ],
}

# ── Trusted Office IPs (allowlist) ────────────────────────────────
TRUSTED_IPS: set[str] = {
    "10.0.0.50",
    "10.0.0.55",
    "10.0.0.60",
    "10.0.0.70",
    "10.0.0.1",     # Office gateway
    "142.44.0.0",   # Known VPN exit for remote employees
}

# ── Safe Domains (known-good list) ────────────────────────────────
SAFE_DOMAINS: set[str] = {
    "corp.com",
    "google.com",
    "github.com",
    "microsoft.com",
    "slack.com",
    "td.com",
}
