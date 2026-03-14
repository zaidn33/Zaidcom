# Sentry AI — Build Plan

> **Goal:** Deliver a demoable, end-to-end AI security triage agent that investigates simulated alerts and executes safe countermeasures, with a polished SOC-style dashboard.

---

## Stage 1 · FastAPI Security Backend & Project Skeleton

**Objective:** Stand up the Python backend, define shared data models, and expose the first API endpoints.

### Tasks
- [ ] Initialize the project with a Python virtual environment and install core dependencies: `fastapi`, `uvicorn`, `pydantic`, `httpx`, `python-dotenv`.
- [ ] Create the project directory structure:
  ```
  server/
  ├── main.py              # FastAPI app entry point
  ├── config.py            # Env vars, API keys, settings
  ├── models/
  │   ├── event.py         # Common Event schema (Pydantic)
  │   ├── case.py          # CaseRecord schema
  │   └── action.py        # ActionResult schema
  ├── routers/
  │   ├── events.py        # POST /api/events, GET /api/events
  │   ├── scenarios.py     # POST /api/scenarios/{name}
  │   ├── cases.py         # GET /api/cases, GET /api/cases/{id}
  │   └── actions.py       # POST /api/actions
  ├── services/
  │   ├── orchestrator.py  # Agent workflow engine
  │   ├── enrichment/      # One client per external API
  │   ├── scoring.py       # Weighted risk scoring
  │   └── action_engine.py # Reversible demo actions
  ├── store/
  │   ├── context.py       # Known devices, login history, allowlists
  │   └── audit.py         # Case & audit trail persistence (SQLite)
  └── fixtures/            # Cached API response fixtures for demo mode
  ```
- [ ] Implement Pydantic models for `Event`, `CaseRecord`, `ToolCall`, and `ActionResult` matching the PRD schemas.
- [ ] Create a basic `/health` endpoint and verify the server starts with `uvicorn`.
- [ ] Set up `.env` for API keys (VirusTotal, AbuseIPDB, IPinfo, vpnapi.io) and a `DEMO_MODE` toggle.

### Deliverable
A running FastAPI server with defined schemas and stub endpoints that accept and return JSON.

---

## Stage 2 · Enrichment Clients, Scenario Simulator & Risk Scoring

**Objective:** Build the external API wrappers, the mock event simulator, and the deterministic scoring engine.

### Tasks
- [ ] **Enrichment Clients** — Create individual async wrappers for each provider behind a common interface:
  | Client             | API            | Returns                              |
  |--------------------|----------------|--------------------------------------|
  | `virustotal.py`    | VirusTotal     | IP/domain/URL reputation             |
  | `abuseipdb.py`     | AbuseIPDB      | Abuse confidence score for IPs       |
  | `ipinfo.py`        | IPinfo         | Geolocation, ASN                     |
  | `vpnapi.py`        | vpnapi.io      | VPN / proxy / Tor flag               |
  - Each client must have: strict timeout (5 s), typed response model, and a **cached fixture fallback** when `DEMO_MODE=true` or on request failure.
- [ ] **Scenario Simulator** — Seed data for three demo scenarios in `fixtures/`:
  | Scenario           | Key signals                                      |
  |--------------------|--------------------------------------------------|
  | Safe Login         | Known user, known device, trusted office IP      |
  | Malicious Login    | Unknown device, RU IP, VPN true                  |
  | Phishing Email     | Typosquatted sender, malicious URL               |
  - `POST /api/scenarios/{name}` returns a normalized `Event` and triggers the pipeline.
- [ ] **Context Store** — In-memory stores for: known devices (by user), recent login history, trusted IP allowlist, prior case outcomes.
- [ ] **Risk Scoring** — Implement the weighted deterministic model from the PRD:
  | Signal                 | Weight |
  |------------------------|--------|
  | Malicious IP           | +35    |
  | VPN / proxy detected   | +15    |
  | Impossible travel      | +25    |
  | Unknown device         | +10    |
  | Failed auth spike      | +10    |
  | Safe allowlist match   | −25    |
  - Classify: **Low** (0–39), **Medium** (40–69), **High** (70–100).

### Deliverable
Scenario simulator endpoints return enriched, scored `CaseRecord` objects with full `toolCalls` arrays.

---

## Stage 3 · Orchestrator & Action Engine

**Objective:** Wire the agentic workflow that receives an event, runs the enrichment chain, scores risk, and executes a safe countermeasure.

### Tasks
- [ ] **Orchestrator (`orchestrator.py`)** — Implement the 9-step agent state machine:
  1. Receive event
  2. Classify event type (`login` | `phishing_email` | `url_click`)
  3. Select tool chain for that event type
  4. Call external enrichment APIs **in parallel** (`asyncio.gather`)
  5. Query internal context store
  6. Correlate signals and compute risk score
  7. Check action guardrails
  8. Execute response or route to analyst
  9. Persist case record to audit store
  - Each step must log a `ToolCall` entry (tool name, status, latency, summary) for the trajectory view.
- [ ] **Action Engine (`action_engine.py`)** — Implement reversible demo actions:
  | Action               | Behavior                                     |
  |----------------------|----------------------------------------------|
  | `block_session`      | Mark session as blocked in state store        |
  | `require_mfa`        | Flag user for MFA on next login               |
  | `quarantine_email`   | Move email to quarantine in simulated mailbox |
  | `block_url`          | Add URL to simulated block policy             |
  | `escalate_to_analyst`| Suppress auto-action, flag for review         |
  | `allow`              | No action taken                               |
  - Each action writes an audit entry and supports **one-click rollback** via `POST /api/actions/{id}/rollback`.
- [ ] **Guardrails** — Hard rules enforced before any action:
  - Never delete accounts, mailboxes, or files.
  - Always require analyst review for privileged / executive accounts.
  - Always persist the reason for every action.
- [ ] **Audit Store** — SQLite-backed persistence for case records and action history.

### Deliverable
`POST /api/scenarios/malicious-login` triggers the full pipeline end-to-end and returns a `CaseRecord` with populated `toolCalls`, `riskScore`, `classification`, `action`, and `actionStatus`.

---

## Stage 4 · React Frontend — Dashboard & Investigation Views

**Objective:** Build the polished SOC-style UI per the Technical Specs (dark mode, Slate palette, Inter font).

### Tasks
- [ ] **Project Setup** — Scaffold with Vite + React + TypeScript. Install dependencies.
- [ ] **Design System** — Implement the color palette and typography from `TECHNICAL_SPECS.md`:
  - Background: `#0F172A`, Surface: `#1E293B`, Borders: `#334155`
  - Text: `#F8FAFC` (primary), `#94A3B8` (secondary)
  - Risk colors: Red `#EF4444`, Amber `#F59E0B`, Emerald `#10B981`
  - Action: Blue `#3B82F6`, System: Violet `#8B5CF6`
  - Font: `Inter` (Google Fonts), 14px body, 20–24px headers
- [ ] **Dashboard View** (matches Figure 1 wireframe):
  - Header bar: "Sentry SOC Dashboard"
  - 5 stat cards row: High Risk, Medium Risk, Low Risk, Auto-Contained, Pending Review
  - Split layout (65/35): Incoming Alerts table (Time, Type, User, Source IP, Risk badge, Action) | Selected Alert Summary panel
  - 3 scenario simulation buttons at bottom of right pane
  - Row selection updates the summary panel
- [ ] **Investigation View** (matches Figure 2 wireframe):
  - Header bar: "Alert Investigation View" with back-to-dashboard nav
  - 3-column layout:
    - **Left:** Event Context (key-value fields)
    - **Middle:** Agent Trajectory (vertical stepper/timeline with connecting line and sequential animation)
    - **Right:** Decision Panel (risk score, classification, reasoning summary, countermeasure buttons, audit trail)
- [ ] **API Integration** — Connect to FastAPI backend:
  - `GET /api/cases` → populate alert list
  - `POST /api/scenarios/{name}` → trigger simulation
  - `GET /api/cases/{id}` → load investigation detail
  - `POST /api/actions` → execute countermeasure
  - `POST /api/actions/{id}/rollback` → rollback action

### Deliverable
A working, visually polished two-view frontend connected to the live backend.

---

## Stage 5 · Polish, Resilience & Demo Prep

**Objective:** Harden the demo, add loading states, fallbacks, and ensure a smooth 5-minute presentation flow.

### Tasks
- [ ] **Loading & Error States** — Skeleton loaders for data fetches, error banners on API failure.
- [ ] **Demo Mode Toggle** — UI switch that forces all enrichment to use cached fixtures (no live API calls).
- [ ] **Trajectory Animation** — Sequentially animate the agent steps on the investigation view to emphasize "agent doing work."
- [ ] **Micro-interactions** — Hover effects on table rows, smooth transitions on panel changes, risk badge pulse animation.
- [ ] **Rollback UI** — One-click rollback button on the investigation view for each executed action.
- [ ] **End-to-End Smoke Test** — Run all three scenarios back-to-back:
  | Scenario        | Expected Risk | Expected Action           |
  |-----------------|---------------|---------------------------|
  | Safe Login      | Low           | Allow (no action)         |
  | Malicious Login | High          | Block session + require MFA |
  | Phishing Email  | High          | Quarantine email          |
- [ ] **Fallback Verification** — Disable internet and verify cached fixtures keep the demo functional.
- [ ] **Backup Demo Recording** — Record a screen capture of the full demo flow as a safety net.

### Deliverable
A fully demoable, resilient Sentry agent ready for hackathon presentation. All three scenarios run cleanly, the UI is polished, and judges can understand the product in under 30 seconds.

---

## Quick Reference — Tech Stack

| Layer        | Technology                                  |
|--------------|---------------------------------------------|
| Backend      | Python 3.11+, FastAPI, Uvicorn, Pydantic    |
| HTTP Client  | httpx (async)                               |
| Database     | SQLite (audit logs & case history)           |
| Frontend     | React 18, TypeScript, Vite                  |
| Styling      | Vanilla CSS (dark mode, Slate palette)       |
| Orchestration| Custom async state machine (or LangGraph)   |
| APIs         | VirusTotal, AbuseIPDB, IPinfo, vpnapi.io    |
