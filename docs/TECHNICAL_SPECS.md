# Sentry UI Technical Specifications

## 1. Overview
This document outlines the technical specifications for building the React frontend of the Sentry SOC agent, based on the provided wireframes and Product Requirements Document (PRD). It is designed to guide the coding agent in creating a highly polished, aesthetic, dark-mode SOC (Security Operations Center) console.

## 2. Design System & Aesthetics
To meet the requirement of a "lightweight SOC console," the UI should utilize a modern, sleek Dark Mode aesthetic. Avoid default generic colors, and apply a sophisticated palette.

### 2.1 Color Palette
*   **Background (App Window)**: `#0F172A` (Slate 900)
*   **Surface/Cards**: `#1E293B` (Slate 800) with subtle `#334155` (Slate 700) borders.
*   **Primary Text**: `#F8FAFC` (Slate 50)
*   **Secondary Text (Labels, Metadata)**: `#94A3B8` (Slate 400)
*   **Risk Indicators (Critical/High)**: `#EF4444` (Red 500)
*   **Risk Indicators (Medium)**: `#F59E0B` (Amber 500)
*   **Risk Indicators (Low/Safe)**: `#10B981` (Emerald 500)
*   **Action/Interactive Elements**: `#3B82F6` (Blue 500) with hover `#2563EB` (Blue 600)
*   **Auto-Contained / System Status**: `#8B5CF6` (Violet 500)

### 2.2 Typography
*   **Font Family**: `Inter` or `Roboto` (sans-serif) for clean readability.
*   **Headers**: Bold (600/700 weight), e.g., sizes like 24px/20px.
*   **Body Text**: Regular (400 weight), 14px size for data tables and logs.

### 2.3 General Layout Rules
*   Padding inside cards should be consistent (e.g., `1.5rem` or 24px).
*   Use flexbox CSS grids to ensure responsive columns.

---

## 3. View 1: Dashboard (Figure 1)
**Purpose:** Provide analysts with an at-a-glance view of incoming alerts, overall threat landscape, and allow quick generation of test scenarios.

### 3.1 Layout & Components
1.  **Top Navigation/Header Bar:** spans full width, title "Sentry SOC Dashboard".
2.  **Stat Cards (Row 1):** Grid of 5 equal-width metric cards.
    *   *High Risk* | *Medium Risk* | *Low Risk* | *Auto-Contained* | *Pending Review*
    *   Each stat card shows a top label and a large number or count/status underneath.
3.  **Main Content Layer:** A split layout (approximately 65% left, 35% right).
    *   **Left Pane (Incoming Alerts Table):**
        *   Columns: `Time`, `Type`, `User`, `Source IP`, `Risk` (Colored badge), `Action`.
        *   Rows must be selectable and hoverable (change background on hover).
    *   **Right Pane (Selected Alert Summary):**
        *   `Risk: <LEVEL>` (e.g., HIGH in red text)
        *   `Evidence`: Bulleted list of context (e.g., VirusTotal flagged IP, VPN / proxy detected, Impossible travel).
        *   `Recommended Action`: Text describing recommended next steps (e.g., Block session, Require MFA reset).
        *   **Bottom Section (Scenario Simulators):** Row of 3 interactive buttons.
            *   `[Simulate Login Attack]`, `[Simulate Phishing]`, `[Replay Safe Event]`.

### 3.2 Logic & Interactivity
*   **State Management:** Create a state variable to hold the currently `selectedAlertId`.
*   **Table Selection:** Clicking a row in the Incoming Alerts table updates the Right Pane's details.
*   **Simulation Buttons:** Hooked up to API calls (simulators) that post mock events to the backend, appending a new alert to the incoming alerts list automatically.

---

## 4. View 2: Alert Investigation (Figure 2)
**Purpose:** The deep-dive view for a specific alert exposing the explicit agent timeline, event context, and final decision panel.

### 3.1 Layout & Components
1.  **Top Navigation/Header Bar:** spans full width, title "Alert Investigation View". Might include a "Back to Dashboard" button.
2.  **Main Content Layer:** A three-column layout (Flexbox: `flex-1` for each column, or approximately 33% / 33% / 33%).
    *   **Left Column (Event Context):**
        *   Displays static structured fields: `Type`, `User`, `Time`, `IP`, `Location`, `Device`, `Privileged User`, `Source`.
        *   Layout as a key-value list with clear vertical spacing.
    *   **Middle Column (Agent Trajectory):**
        *   A vertical timeline or stack of rectangular cards/pills representing the chain of agent logic.
        *   List of steps from "1. Receive event..." to "9. Write case record...".
        *   *Aesthetic Requirement:* Give these steps subtle directional arrows or a connecting vertical line like a roadmap/stepper to show progression.
    *   **Right Column (Decision Panel):**
        *   `Risk Score`: `<score> / 100` (color-coded, e.g., Red for 91/100).
        *   `Classification`: (e.g., High).
        *   `Reasoning Summary`: Brief paragraph explaining the AI's logic.
        *   `Safe Countermeasures`: A dedicated group of buttons to manually trigger fallback or additional actions: `[Block Session]`, `[Require MFA]`, `[Disable token refresh]`, `[Escalate to analyst]`.
        *   `Audit Trail`: Timestamp and message showing automated policies that ran.

### 4.2 Logic & Interactivity
*   **Trajectory Animation:** If possible, when loading this view, animate the middle column steps rendering sequentially to emphasize the "agent doing work" aspect.
*   **Countermeasure Execution:** Secondary action buttons should trigger server-side updates (e.g., POST to `/api/action`) and update the UI with a success/loading state.
*   **Navigation:** Connects directly from the "Incoming Alerts" table (User double-clicks row or clicks "Investigate" button on alert details).
