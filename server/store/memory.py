"""
Sentry AI — In-Memory Store
Singleton holding all runtime state for the hackathon MVP.
Persisted only for the lifetime of the server process.
"""

from models.event import Event
from models.case import CaseRecord
from models.action import ActionResult


class MemoryStore:
    """Thread-safe in-memory store for events, cases, and actions."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._cases: list[CaseRecord] = []
        self._actions: list[ActionResult] = []

    # ── Events ────────────────────────────────────────────────────
    def add_event(self, event: Event) -> Event:
        self._events.append(event)
        return event

    def get_event(self, event_id: str) -> Event | None:
        return next((e for e in self._events if e.event_id == event_id), None)

    def list_events(self) -> list[Event]:
        return list(self._events)

    # ── Cases ─────────────────────────────────────────────────────
    def add_case(self, case: CaseRecord) -> CaseRecord:
        self._cases.append(case)
        return case

    def get_case(self, case_id: str) -> CaseRecord | None:
        return next((c for c in self._cases if c.case_id == case_id), None)

    def list_cases(self) -> list[CaseRecord]:
        return list(self._cases)

    # ── Actions ───────────────────────────────────────────────────
    def add_action(self, action: ActionResult) -> ActionResult:
        self._actions.append(action)
        return action

    def get_action(self, action_id: str) -> ActionResult | None:
        return next(
            (a for a in self._actions if a.action_id == action_id), None
        )

    def list_actions(self) -> list[ActionResult]:
        return list(self._actions)


# Global singleton — initialised once at startup
store = MemoryStore()
