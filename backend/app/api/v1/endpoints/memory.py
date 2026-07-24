import uuid
from fastapi import APIRouter, Depends
from backend.app.api.dependencies import get_mongo_service, get_chroma_service, get_current_client_id
from backend.app.services.mongo_service import MongoService
from backend.app.services.chroma_service import ChromaMemoryLayer
from backend.app.schemas.memory_schemas import MemoryValidateRequestModel, MemoryValidateResponseModel
from backend.app.core.exceptions import SecurityError

router = APIRouter()


@router.post("/memory/validate", response_model=MemoryValidateResponseModel)
async def validate_memory_preference(
    payload: MemoryValidateRequestModel,
    mongo: MongoService = Depends(get_mongo_service),
    chroma: ChromaMemoryLayer = Depends(get_chroma_service),
    auth_client_id: str = Depends(get_current_client_id)
):
    """Transition notification to approved/rejected state and write to offline vector space if approved."""
    if payload.client_id != auth_client_id:
        raise SecurityError("Tenant isolation mismatch")

    state_map = {"approve": "approved", "reject": "rejected"}
    current_state = state_map.get(payload.action, "approved")

    # Step 1: Update status state inside MongoDB Atlas
    mongo.update_notification(
        notification_id=payload.notification_id,
        client_id=payload.client_id,
        status=current_state
    )

    chroma_id = None
    if payload.action == "approve":
        # Generate a unique memory trace ID
        chroma_id = f"mem_{uuid.uuid4().hex[:8]}"
        # Step 2: Store distilled preference sentence inside local offline vector collections
        await chroma.add_client_fact(
            client_id=payload.client_id,
            fact_id=chroma_id,
            fact_text=payload.extracted_fact,
            domain=payload.domain
        )

    return MemoryValidateResponseModel(
        status="success",
        notification_id=payload.notification_id,
        current_state=current_state,
        chroma_id=chroma_id
    )


@router.get("/memory/pending")
async def list_pending_validations(
    client_id: str,
    mongo: MongoService = Depends(get_mongo_service),
    auth_client_id: str = Depends(get_current_client_id)
):
    """Retrieves list of pending human-in-the-loop validation notifications."""
    if client_id != auth_client_id:
        raise SecurityError("Tenant isolation mismatch")

    notifications = mongo.get_pending_notifications(client_id=client_id)
    return notifications
