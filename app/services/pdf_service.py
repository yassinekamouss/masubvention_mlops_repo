import os
import re
import logging
from typing import List, Optional, Dict, Any
import pdfplumber

from app.schemas.legal import EntrepriseLegalInfo

logger = logging.getLogger(__name__)


def parse_legal_info_heuristics(text: str) -> Dict[str, Any]:
    """Extraction heuristique regex pour garantir la résilience même sans LLM."""
    info = {
        "nom": "Non renseigné",
        "ice": "Non renseigné",
        "rc": "Non renseigné",
        "identifiant_fiscal": "Non renseigné",
        "cnss": "Non renseigné",
        "forme_juridique": "Non renseigné",
        "activite_statutaire": "Non renseigné",
        "date_creation": "Non renseigné",
        "branche_activite": "Non renseigné",
        "activite_detaillee": "Non renseigné",
        "capital_social": "Non renseigné",
        "actionnaires": "Non renseigné",
        "representant_legal": "Non renseigné",
        "adresse_siege": "Non renseigné",
        "coordonnees_gps": "Non renseigné",
        "branche_activite_projet": "Non renseigné",
        "biens_services": "Non renseigné",
        "ca_2023": "Non renseigné",
        "ca_2024": "Non renseigné",
        "ca_2025": "Non renseigné",
    }

    if not text:
        return info

    # ICE (9 à 15 chiffres)
    ice_match = re.search(r'\b(?:ICE|I\.C\.E\.|IDENTIFIANT\s+COMMUN)\b[^\d\n]*?([0-9]{9,15})', text, re.IGNORECASE)
    if ice_match:
        info["ice"] = ice_match.group(1).strip()

    # Registre du Commerce (RC)
    rc_match = re.search(r'\b(?:RC|R\.C\.|REGISTRE\s+DU\s+COMMERCE)\b[^\d\n]*?([0-9]{3,10})', text, re.IGNORECASE)
    if rc_match:
        info["rc"] = rc_match.group(1).strip()

    # Identifiant Fiscal (IF)
    if_match = re.search(r'\b(?:IF|I\.F\.|IDENTIFIANT\s+FISCAL)\b[^\d\n]*?([0-9]{6,10})', text, re.IGNORECASE)
    if if_match:
        info["identifiant_fiscal"] = if_match.group(1).strip()

    # CNSS (6 à 10 chiffres)
    cnss_match = re.search(r'\b(?:CNSS|C\.N\.S\.S\.|AFFILIATION)\b[^\d\n]*?([0-9]{6,10})', text, re.IGNORECASE)
    if cnss_match:
        info["cnss"] = cnss_match.group(1).strip()

    # Forme juridique
    if re.search(r'\b(SARL\s*AU|S\.A\.R\.L\s*A\.U)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SARL AU"
    elif re.search(r'\b(SARL|S\.A\.R\.L)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SARL"
    elif re.search(r'\b(SA|S\.A\.)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SA"
    elif re.search(r'\b(SAS|S\.A\.S)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SAS"

    # Capital social
    cap_match = re.search(r'(?:CAPITAL(?:\s+SOCIAL)?)[^\d\n]*([0-9\s.,]+)\s*(?:DH|MAD)', text, re.IGNORECASE)
    if cap_match:
        cap_val = re.sub(r'[^\d]', '', cap_match.group(1))
        if cap_val:
            info["capital_social"] = f"{int(cap_val):,}".replace(",", " ")

    # Date creation (JJ/MM/AAAA)
    date_match = re.search(r'(?:DATE(?:\s+DE)?\s+CR[EÉ]ATION|CR[EÉ][EÉ]E?\s+LE)[\s:.\-#]*([0-9]{2}[/-][0-9]{2}[/-][0-9]{4})', text, re.IGNORECASE)
    if date_match:
        info["date_creation"] = date_match.group(1).strip()

    # Nom / Dénomination
    denom_match = re.search(r'(?:D[EÉ]NOMINATION|RAISON\s+SOCIALE)[\s:.\-#]*([A-Z0-9\s&\'\.-]{3,50})', text, re.IGNORECASE)
    if denom_match:
        info["nom"] = denom_match.group(1).strip()

    # Adresse siège
    siege_match = re.search(r'(?:SI[EÈ]GE\s+SOCIAL|ADRESSE)[\s:.\-#]*([^\n]{5,80})', text, re.IGNORECASE)
    if siege_match:
        info["adresse_siege"] = siege_match.group(1).strip()

    return info


class PdfParserService:
    """Service dedicated to reading Moroccan administrative PDF files and extracting structured legal data."""

    @staticmethod
    def read_pdf_files(file_paths: List[str], dossier_id: int = 0) -> str:
        """Extracts text content from multiple PDF documents using pdfplumber."""
        combined_text = ""
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    with pdfplumber.open(path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                combined_text += page_text + "\n"
                except Exception as e:
                    logger.error(f"[{dossier_id}] Erreur lecture PDF {path}: {e}")
            else:
                if path:
                    logger.warning(f"[{dossier_id}] Fichier introuvable : {path}")

        return combined_text

    @classmethod
    def extract_legal_info(
        cls,
        file_paths: List[str],
        llm: Optional[Any] = None,
        dossier_id: int = 0
    ) -> Dict[str, Any]:
        """Combines pdf text extraction, regex heuristics and structured LLM extraction."""
        combined_text = cls.read_pdf_files(file_paths, dossier_id=dossier_id)
        logger.info(f"[{dossier_id}] {len(combined_text)} caractères extraits des PDF.")

        # 1. Extraction regex heuristique systématique
        regex_extracted = parse_legal_info_heuristics(combined_text)

        # 2. Appel LLM si disponible et contenu présent
        pdf_info = None
        if llm and len(combined_text.strip()) > 10:
            try:
                structured_llm = llm.with_structured_output(EntrepriseLegalInfo)
                prompt = (
                    "Tu es un expert en analyse documentaire juridique et fiscale marocaine.\n"
                    "Extrait précisément les informations administratives, juridiques et fiscales de l'entreprise "
                    "à partir du texte ci-dessous issu des attestations officielles (Attestation Fiscale, Registre de Commerce, CNSS).\n"
                    "Si une information est introuvable, indique 'Non renseigné'.\n\n"
                    f"Texte des documents administratifs:\n{combined_text[:12000]}"
                )
                result = structured_llm.invoke(prompt)
                pdf_info = result.model_dump() if hasattr(result, 'model_dump') else dict(result)
                logger.info(f"[{dossier_id}] Extraction LLM réussie pour : {pdf_info.get('nom')}")
            except Exception as e:
                logger.warning(f"[{dossier_id}] Erreur lors de l'extraction LLM: {e}. Utilisation du parseur heuristique.")

        if not pdf_info:
            pdf_info = regex_extracted
        else:
            # Compléter les champs manquants avec les heuristiques
            for k, v in regex_extracted.items():
                if pdf_info.get(k) in [None, "", "Non renseigné"] and v != "Non renseigné":
                    pdf_info[k] = v

        return pdf_info
