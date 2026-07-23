import time
from fastapi import APIRouter, Depends
from backend.app.api.dependencies import get_mongo_service
from backend.app.services.mongo_service import MongoService
from backend.app.schemas.reports_schemas import SaveReportRequestModel, SaveReportResponseModel

router = APIRouter()

@router.post("/reports/save", response_model=SaveReportResponseModel)
async def save_report_canvas(
    payload: SaveReportRequestModel,
    mongo: MongoService = Depends(get_mongo_service)
):
    """Saves structural Tiptap document canvas payload in MongoDB Atlas and returns tracking ID."""
    report_id = mongo.save_report(
        client_id=payload.client_id,
        report_name=payload.report_name,
        tiptap_json=payload.tiptap_json.model_dump(mode="json")
    )

    return SaveReportResponseModel(
        status="success",
        report_id=report_id,
        saved_at=int(time.time())
    )
