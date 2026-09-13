from typing_extensions import TypedDict
from typing import Dict, Any


class WorkflowState(TypedDict):
    """Execution state passed between LangGraph nodes during investment dossier analysis."""
    dossier_id: int
    file_paths: Dict[str, Any]
    financial_data: Dict[str, Any]
    pdf_extracted_info: Dict[str, Any]
    narrative_report: Dict[str, Any]
    final_json: Dict[str, Any]
