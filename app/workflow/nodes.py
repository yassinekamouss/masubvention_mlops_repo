import logging
from app.workflow.state import WorkflowState
from app.core.llm_factory import LLMFactory
from app.services.pdf_service import PdfParserService
from app.services.consultant_service import VirtualConsultantService
from app.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


def extract_pdf_llm_node(state: WorkflowState) -> dict:
    """Node 1: Extract text from administrative PDFs and extract legal info via LLM / regex heuristics."""
    dossier_id = state.get("dossier_id", 0)
    logger.info(f"[{dossier_id}] [Node 1: extract_pdf_llm] Lecture des PDF et extraction juridique/fiscale...")

    file_paths = state.get("file_paths", {})
    pdf_paths = [
        file_paths.get("file_fiscale"),
        file_paths.get("file_rc"),
        file_paths.get("file_cnss"),
    ]

    llm = LLMFactory.get_llm()
    pdf_info = PdfParserService.extract_legal_info(
        file_paths=pdf_paths,
        llm=llm,
        dossier_id=dossier_id
    )

    return {"pdf_extracted_info": pdf_info}


def virtual_consultant_node(state: WorkflowState) -> dict:
    """Node 2: The Virtual Consultant drafts 4 high-value strategic investment memorandum sections."""
    dossier_id = state.get("dossier_id", 0)
    logger.info(f"[{dossier_id}] [Node 2: virtual_consultant] Rédaction des argumentaires d'investissement...")

    pdf_info = state.get("pdf_extracted_info", {})
    financial_data = state.get("financial_data", {})
    llm = LLMFactory.get_llm()

    narratives = VirtualConsultantService.generate_narratives(
        pdf_info=pdf_info,
        financial_data=financial_data,
        llm=llm,
        dossier_id=dossier_id
    )

    return {"narrative_report": narratives}


def consolidate_webhook_node(state: WorkflowState) -> dict:
    """Node 3: Consolidates final JSON structure and notifies Express backend via HTTP webhook."""
    dossier_id = state.get("dossier_id", 0)
    logger.info(f"[{dossier_id}] [Node 3: consolidate_webhook] Consolidation du rapport et envoi webhook...")

    pdf_info = state.get("pdf_extracted_info", {})
    financial_data = state.get("financial_data", {})
    narratives = state.get("narrative_report", {})

    final_json = WebhookService.build_consolidated_json(
        pdf_info=pdf_info,
        financial_data=financial_data,
        narratives=narratives
    )

    WebhookService.send_webhook(
        dossier_id=dossier_id,
        final_json=final_json
    )

    return {"final_json": final_json}
