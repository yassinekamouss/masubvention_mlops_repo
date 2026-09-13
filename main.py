import uvicorn
from app import create_app
from app.core.config import settings
from app.workflow import workflow_graph, process_dossier_task
from app.schemas import (
    ExtractionFiles,
    ExtractionRequest,
    ExtractionResponse,
    EntrepriseLegalInfo,
    NarrativeReport,
)
from app.services.pdf_service import parse_legal_info_heuristics

# Initialize application instance via application factory
app = create_app()

# Backward compatibility exports for existing scripts and test runners
__all__ = [
    "app",
    "workflow_graph",
    "process_dossier_task",
    "ExtractionFiles",
    "ExtractionRequest",
    "ExtractionResponse",
    "EntrepriseLegalInfo",
    "NarrativeReport",
    "parse_legal_info_heuristics",
]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )
