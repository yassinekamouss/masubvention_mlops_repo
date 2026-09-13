from pydantic import BaseModel, Field


class EntrepriseLegalInfo(BaseModel):
    """Structured legal, tax and administrative information of the enterprise."""
    nom: str = Field(default="Non renseigné", description="Raison sociale de l'entreprise")
    ice: str = Field(default="Non renseigné", description="Identifiant Commun de l'Entreprise (ICE)")
    rc: str = Field(default="Non renseigné", description="Registre du Commerce (RC)")
    identifiant_fiscal: str = Field(default="Non renseigné", description="Identifiant Fiscal (IF)")
    cnss: str = Field(default="Non renseigné", description="Numéro d'affiliation CNSS")
    forme_juridique: str = Field(default="Non renseigné", description="Forme juridique (ex: SARL, SA, etc.)")
    activite_statutaire: str = Field(default="Non renseigné", description="Activité de la société conforme aux statuts")
    date_creation: str = Field(default="Non renseigné", description="Date de création de l'entreprise")
    branche_activite: str = Field(default="Non renseigné", description="Secteur ou branche d'activité de l'entreprise")
    activite_detaillee: str = Field(default="Non renseigné", description="Description détaillée de l'activité ou des services")
    capital_social: str = Field(default="Non renseigné", description="Montant du capital social en MAD")
    actionnaires: str = Field(default="Non renseigné", description="Liste des actionnaires principaux")
    representant_legal: str = Field(default="Non renseigné", description="Nom du représentant légal ou gérant")
    adresse_siege: str = Field(default="Non renseigné", description="Adresse complète du siège social")
    coordonnees_gps: str = Field(default="Non renseigné", description="Coordonnées GPS ou adresse du projet")
    branche_activite_projet: str = Field(default="Non renseigné", description="Branche d'activité du projet d'investissement")
    biens_services: str = Field(default="Non renseigné", description="Biens et/ou services produits par le projet")
    ca_2023: str = Field(default="Non renseigné", description="Chiffre d'affaires de l'année 2023 en MAD")
    ca_2024: str = Field(default="Non renseigné", description="Chiffre d'affaires de l'année 2024 en MAD")
    ca_2025: str = Field(default="Non renseigné", description="Chiffre d'affaires de l'année 2025 en MAD")
