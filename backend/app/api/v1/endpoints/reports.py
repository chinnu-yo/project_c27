import time
from fastapi import APIRouter, Depends, BackgroundTasks
from backend.app.api.dependencies import get_mongo_service, get_critic_service
from backend.app.services.mongo_service import MongoService
from backend.app.services.critic_service import CriticService
from backend.app.schemas.reports_schemas import SaveReportRequestModel, SaveReportResponseModel

router = APIRouter()

@router.post("/reports/save", response_model=SaveReportResponseModel)
async def save_report_canvas(
    payload: SaveReportRequestModel,
    background_tasks: BackgroundTasks,
    mongo: MongoService = Depends(get_mongo_service),
    critic: CriticService = Depends(get_critic_service)
):
    """Saves structural Tiptap document canvas payload in MongoDB Atlas and returns tracking ID."""
    tiptap_dict = payload.tiptap_json.model_dump(mode="json")
    report_id = mongo.save_report(
        client_id=payload.client_id,
        report_name=payload.report_name,
        tiptap_json=tiptap_dict
    )

    # Trigger background Critic review for rule learning on manually saved canvases
    background_tasks.add_task(
        critic.run_async_critic,
        payload.client_id,
        tiptap_dict
    )

    return SaveReportResponseModel(
        status="success",
        report_id=report_id,
        saved_at=int(time.time())
    )

