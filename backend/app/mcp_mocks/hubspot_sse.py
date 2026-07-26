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

from typing import Dict, Any, List
from backend.app.core.exceptions import ValidationError

HUBSPOT_DATABASE: Dict[str, Dict[str, Any]] = {
    "client_abc": {
        "active_deals": [
            {"deal_id": "deal_551", "deal_name": "ACME Enterprise Renewal", "amount": 80000.0, "stage": "Closed Won", "owner": "Alice Miller"},
            {"deal_id": "deal_552", "deal_name": "Q4 Expansion Retainer", "amount": 25000.0, "stage": "Proposal Sent", "owner": "Sarah Connor"}
        ],
        "total_pipeline_value": 105000.0,
        "lead_stage": "Enterprise Account",
        "account_owner": "Alice Miller"
    },
    "client_xyz": {
        "active_deals": [
            {"deal_id": "deal_901", "deal_name": "XYZ Platform Setup", "amount": 45000.0, "stage": "Negotiation", "owner": "John Doe"}
        ],
        "total_pipeline_value": 45000.0,
        "lead_stage": "Opportunity",
        "account_owner": "John Doe"
    }
}

def get_hubspot_data(client_id: str) -> Dict[str, Any]:
    """Retrieves mock HubSpot CRM deal values, lead stages, and account owner information."""
    if not client_id:
        raise ValidationError("client_id parameter is required for HubSpot lookup.")
    return HUBSPOT_DATABASE.get(client_id, {
        "active_deals": [],
        "total_pipeline_value": 0.0,
        "lead_stage": "Unassigned",
        "account_owner": "Unassigned"
    })

@router.get("/stream")
async def get_crm_stream():
    """Endpoint allowing Next.js or Orchestrator to read live CRM update feeds."""
    return StreamingResponse(mock_crm_events(), media_type="text/event-stream")
