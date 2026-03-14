import asyncio
import os
import sys

# Add server to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from store.audit import get_action_for_case
from services.action_engine import rollback_action

async def test_rollback():
    # Find the malicious_login case ID from cases.json
    case_id = "SENTRY-CA9299A1" # Hardcoded from cases.json inspection
    print(f"Fetching action for Case ID: {case_id}")
    action = await get_action_for_case(case_id)
    if not action:
        print("Action not found!")
        return

    print(f"Original Action: {action.action_type.value}, Status: {action.status}")
    print(f"Rolling back action {action.action_id}...")
    rolled_back = await rollback_action(action)
    print(f"New Status: {rolled_back.status}")
    print(f"New Reason: {rolled_back.reason}")

if __name__ == "__main__":
    asyncio.run(test_rollback())
