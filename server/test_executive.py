import asyncio
import os
import sys

# Add server to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.event import Event, EventType
from services.orchestrator import investigate

async def test_executive():
    event = Event(
        event_type=EventType.LOGIN,
        user="alice@corp.com",       # Alice is an EXECUTIVE
        source_ip="185.220.101.1",   # Malicious IP (VT = 12, AbuseIPDB = 95%)
        device_id="unknown-device-99"
    )
    
    print(f"Testing Executive login: {event.user} from {event.source_ip}")
    case = await investigate(event)
    print(f"Result Case ID: {case.case_id}")
    print(f"Risk Score: {case.risk_score} ({case.classification.value})")
    print(f"Action Taken: {case.action}")
    print(f"Action Status: {case.action_status}")
    print(f"Reasoning: {case.reasoning}")

if __name__ == "__main__":
    asyncio.run(test_executive())
