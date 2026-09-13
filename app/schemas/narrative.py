from pydantic import BaseModel, Field


class NarrativeReport(BaseModel):
    """Four mandatory strategic narrative sections drafted by the Virtual Consultant."""
    presentation_projet: str = Field(
        default="",
        description="Synthèse de l'opportunité d'investissement et alignement stratégique avec la Charte de l'Investissement"
    )
    coherence_territoriale: str = Field(
        default="",
        description="Justification de l'implantation territoriale et conformité aux objectifs régionaux"
    )
    impact_socio_economique_argumentaire: str = Field(
        default="",
        description="Création d'emplois locaux pérennes, parité, inclusion et démarche environnementale"
    )
    viabilite_financiere: str = Field(
        default="",
        description="Rentabilité prévisionnelle, solidité du montage financier et capacité d'autofinancement"
    )
