from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ExtractionFiles(BaseModel):
    """File paths for the 3 required Moroccan administrative PDFs."""
    file_fiscale: str = Field(default="", description="Chemin vers l'Attestation Fiscale")
    file_rc: str = Field(default="", description="Chemin vers le Registre de Commerce (RC)")
    file_cnss: str = Field(default="", description="Chemin vers l'Attestation d'Affiliation CNSS")


class ExtractionRequest(BaseModel):
    """Payload received from the Express backend to trigger analysis."""
    dossierId: int = Field(..., description="ID unique du dossier d'investissement")
    files: ExtractionFiles = Field(..., description="Chemins d'accès aux pièces justificatives")
    financial_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Grille financière déterministe précalculée par le moteur Express"
    )


class ExtractionResponse(BaseModel):
    """Response returned synchronously to acknowledge task start."""
    status: str = Field(default="processing", description="Statut du traitement")
    message: str = Field(..., description="Message informatif")
    dossierId: int = Field(..., description="ID du dossier en cours")
