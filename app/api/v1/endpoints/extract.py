import logging
from fastapi import APIRouter, BackgroundTasks

from app.schemas.extraction import ExtractionRequest
from app.workflow.graph import process_dossier_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract", tags=["Extraction"])
async def extract_dossier(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks
):
    """
    Receives dossier files and pre-calculated financial data, and launches
    the asynchronous LangGraph analysis and narrative generation pipeline.
    """
    files_dict = request.files.model_dump() if hasattr(request.files, 'model_dump') else request.files.dict()
    financial_dict = request.financial_data or {}
    stepper_dict = request.stepper_data or {}
    test_dict = request.test_data or {}
    client_dict = request.client_info or {}

    background_tasks.add_task(
        process_dossier_task,
        request.dossierId,
        files_dict,
        financial_dict,
        stepper_dict,
        test_dict,
        client_dict
    )

    logger.info(f"Dossier #{request.dossierId} queued for background AI processing.")

    return {
        "status": "processing",
        "message": f"Dossier {request.dossierId} received. AI extraction pipeline started.",
        "dossierId": request.dossierId
    }
