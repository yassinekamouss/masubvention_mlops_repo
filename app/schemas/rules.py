from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ProfileRuleSchema(BaseModel):
    """Schema representing an individual DNF Eligibility Profile matching the Frontend cards."""
    id: Optional[str] = Field(default=None, description="Identifiant unique du profil")
    name: str = Field(default="Profil 1", description="Nom descriptif du profil")

    # 1. Territoire & Régions
    regionsMode: Literal["ALL", "SPECIFIC"] = Field(
        default="ALL",
        description="Mode de sélection des régions ('ALL' ou 'SPECIFIC')"
    )
    regions: List[str] = Field(
        default_factory=list,
        description="Liste des régions éligibles (strictement parmi les 12 régions marocaines)"
    )

    # 2. Secteurs d'activité
    secteursMode: Literal["ALL", "SPECIFIC"] = Field(
        default="ALL",
        description="Mode de sélection des secteurs ('ALL' ou 'SPECIFIC')"
    )
    secteurs: List[str] = Field(
        default_factory=list,
        description="Liste des codes de secteurs d'activité éligibles"
    )

    # 3. Forme Juridique & Applicant
    applicantType: Literal["ALL", "morale", "physique"] = Field(
        default="ALL",
        description="Type de demandeur ('ALL', 'morale' ou 'physique')"
    )
    statutsMode: Literal["ALL", "SPECIFIC"] = Field(
        default="ALL",
        description="Mode de sélection des statuts ('ALL' ou 'SPECIFIC')"
    )
    statuts: List[str] = Field(
        default_factory=list,
        description="Formes juridiques (ex: ['sarl', 'sarlau', 'societe-sas'])"
    )
    ageMin: Optional[int] = Field(default=None, description="Âge minimum du dirigeant (personne physique)")
    ageMax: Optional[int] = Field(default=None, description="Âge maximum du dirigeant (personne physique)")
    hasNoAgeLimit: bool = Field(default=True, description="Aucune limite d'âge si True")
    sexe: Literal["ALL", "homme", "femme"] = Field(default="ALL", description="Genre ciblé")

    # 4. Maturité & Âge entreprise
    creationMode: Literal["ALL", "NEW_UNDER_3", "ESTABLISHED_OVER_3", "CUSTOM"] = Field(
        default="ALL",
        description="Critère d'ancienneté ('ALL', 'NEW_UNDER_3', 'ESTABLISHED_OVER_3', 'CUSTOM')"
    )
    creationYears: List[str] = Field(
        default_factory=list,
        description="Années de création si CUSTOM (ex: ['2025', '2024'])"
    )

    # 5. Envergure Financière & Effectifs
    caMin: Optional[float] = Field(default=None, description="Chiffre d'affaires minimum en MAD")
    caMax: Optional[float] = Field(default=None, description="Chiffre d'affaires maximum en MAD")
    hasNoCaMax: bool = Field(default=True, description="Pas de plafond de CA si True")
    investissements: List[str] = Field(
        default_factory=list,
        description="Tranches d'investissement (ex: ['1M-10M', '10M-20M'])"
    )
    employees: List[str] = Field(
        default_factory=list,
        description="Tranches d'effectifs (ex: ['entre 1 et 3 employés', 'plus de 10 employés'])"
    )


class MagicRuleRequest(BaseModel):
    """Admin natural language request to generate eligibility rules."""
    prompt: str = Field(..., description="Description en langage naturel des conditions d'éligibilité")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Contexte optionnel du programme (nom, description)"
    )


class MagicRuleResponse(BaseModel):
    """Structured response containing interpreted DNF profiles."""
    success: bool = Field(default=True, description="Indique si la génération a réussi")
    summary: str = Field(..., description="Synthèse explicative en 1-2 phrases des règles générées")
    profiles: List[ProfileRuleSchema] = Field(
        default_factory=list,
        description="Tableau des profils d'éligibilité DNF (chaque profil est une conjonction ET, liés par des OU)"
    )
