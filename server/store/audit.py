from typing import List, Dict, Any, Optional
from typing import Optional, List, Dict, Any
"""
Sentry AI — SQLite Audit Store
Persists Cases and Action history locally for the demo dashboard.
Provides accurate timestamps for 'Time to Mitigation' calculations.
"""

import json
import logging
from typing import Any

import aiosqlite

from config import settings
from models.case import CaseRecord, RiskClassification
from models.action import ActionResult, ActionType

logger = logging.getLogger("sentry.store.audit")

DATABASE_URL = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")


async def init_db() -> None:
    """Initialize SQLite database schemas if they don't exist."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                classification TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                signals JSON NOT NULL,
                tool_calls JSON NOT NULL,
                action TEXT NOT NULL,
                action_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS actions (
                action_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                reversible BOOLEAN NOT NULL,
                executed_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(case_id)
            )
            """
        )
        await db.commit()
    logger.info("SQLite audit store initialized at %s", DATABASE_URL)


async def save_case(case: CaseRecord) -> None:
    """Upsert a fully populated CaseRecord, updating Time to Mitigate if present."""
    signals_json = json.dumps(case.signals)
    tools_json = json.dumps([tc.model_dump() for tc in case.tool_calls])

    query = """
    INSERT INTO cases (
        case_id, event_id, risk_score, classification, reasoning,
        signals, tool_calls, action, action_status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(case_id) DO UPDATE SET
        risk_score = excluded.risk_score,
        classification = excluded.classification,
        reasoning = excluded.reasoning,
        signals = excluded.signals,
        tool_calls = excluded.tool_calls,
        action = excluded.action,
        action_status = excluded.action_status,
        updated_at = excluded.updated_at
    """
    
    params = (
        case.case_id, case.event_id, case.risk_score, case.classification.value,
        case.reasoning, signals_json, tools_json, case.action, case.action_status,
        case.created_at, case.updated_at
    )

    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(query, params)
            await db.commit()
    except Exception as exc:
        logger.error("Failed to save CaseRecord %s: %s", case.case_id, exc)


async def get_case(case_id: str) -> Optional[CaseRecord]:
    """Fetch a single CaseRecord by ID."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return CaseRecord(
                case_id=row["case_id"],
                event_id=row["event_id"],
                risk_score=row["risk_score"],
                classification=RiskClassification(row["classification"]),
                reasoning=row["reasoning"],
                signals=json.loads(row["signals"]),
                tool_calls=json.loads(row["tool_calls"]),
                action=row["action"],
                action_status=row["action_status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )


async def list_cases(limit: int = 50) -> List[CaseRecord]:
    """Retrieve the latest cases for the dashboard."""
    cases = []
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM cases ORDER BY created_at DESC LIMIT ?", (limit,)) as cursor:
            async for row in cursor:
                cases.append(CaseRecord(
                    case_id=row["case_id"],
                    event_id=row["event_id"],
                    risk_score=row["risk_score"],
                    classification=RiskClassification(row["classification"]),
                    reasoning=row["reasoning"],
                    signals=json.loads(row["signals"]),
                    tool_calls=json.loads(row["tool_calls"]),
                    action=row["action"],
                    action_status=row["action_status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                ))
    return cases


async def save_action(action: ActionResult) -> None:
    """Insert or update an action record."""
    query = """
    INSERT INTO actions (
        action_id, case_id, action_type, status, reason, reversible, executed_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(action_id) DO UPDATE SET
        status = excluded.status
    """
    params = (
        action.action_id, action.case_id, action.action_type.value,
        action.status, action.reason, action.reversible, action.executed_at
    )
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(query, params)
            await db.commit()
    except Exception as exc:
        logger.error("Failed to save ActionResult %s: %s", action.action_id, exc)


async def get_action_for_case(case_id: str) -> Optional[ActionResult]:
    """Get the action associated with a specific case."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM actions WHERE case_id = ?", (case_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return ActionResult(
                action_id=row["action_id"],
                case_id=row["case_id"],
                action_type=ActionType(row["action_type"]),
                status=row["status"],
                reason=row["reason"],
                reversible=row["reversible"],
                executed_at=row["executed_at"]
            )
