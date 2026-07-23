import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/hubspot", tags=["HubSpot Mock"])

async def mock_crm_events():
    """Generates server-sent events detailing mock HubSpot CRM deal transitions."""
    events = [
        {"event": "deal_updated", "deal_id": "deal_551", "deal_name": "ACME Renewal", "amount": 8000.0, "stage": "Closed Won"},
        {"event": "deal_created", "deal_id": "deal_552", "deal_name": "Globex Expansion", "amount": 14500.0, "stage": "Proposal Sent"},
        {"event": "contact_added", "contact_id": "cont_901", "name": "Sarah Connor", "email": "sarah@resistance.org"}
    ]
    for event in events:
        # Format matching SSE spec (data: JSON_PAYLOAD\n\n)
        yield f"data: {json.dumps(event)}\n\n"
        await asyncio.sleep(2)  # Delay between events

@router.get("/stream")
async def get_crm_stream():
    """Endpoint allowing Next.js or Orchestrator to read live CRM update feeds."""
    return StreamingResponse(mock_crm_events(), media_type="text/event-stream")
