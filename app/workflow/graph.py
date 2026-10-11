import logging
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, START, END

from app.workflow.state import WorkflowState
from app.workflow.nodes import (
    extract_pdf_llm_node,
    virtual_consultant_node,
    consolidate_webhook_node,
)

logger = logging.getLogger(__name__)


def build_workflow_graph():
    """Builds and compiles the StateGraph workflow for investment dossier analysis."""
    builder = StateGraph(WorkflowState)

    # 1. Register processing nodes
    builder.add_node("extract_pdf_llm", extract_pdf_llm_node)
    builder.add_node("virtual_consultant", virtual_consultant_node)
    builder.add_node("consolidate_webhook", consolidate_webhook_node)

    # 2. Define sequential execution flow
    builder.add_edge(START, "extract_pdf_llm")
    builder.add_edge("extract_pdf_llm", "virtual_consultant")
    builder.add_edge("virtual_consultant", "consolidate_webhook")
    builder.add_edge("consolidate_webhook", END)

    return builder.compile()


# Global compiled workflow instance
workflow_graph = build_workflow_graph()


def process_dossier_task(
    dossier_id: int,
    files: Dict[str, Any],
    financial_data: Optional[Dict[str, Any]] = None,
    stepper_data: Optional[Dict[str, Any]] = None,
    test_data: Optional[Dict[str, Any]] = None,
    client_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Background task runner executing the LangGraph pipeline for a specific dossier."""
    initial_state: WorkflowState = {
        "dossier_id": dossier_id,
        "file_paths": files or {},
        "financial_data": financial_data or {},
        "stepper_data": stepper_data or {},
        "test_data": test_data or {},
        "client_info": client_info or {},
        "pdf_extracted_info": {},
        "narrative_report": {},
        "final_json": {},
    }
    logger.info(f"Starting LangGraph execution for Dossier #{dossier_id}")
    final_output = workflow_graph.invoke(initial_state)
    logger.info(f"Finished LangGraph execution for Dossier #{dossier_id}")
    return final_output
