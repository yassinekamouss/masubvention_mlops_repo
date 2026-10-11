import os
import re
import logging
from typing import List, Optional, Dict, Any
import pdfplumber

from app.schemas.legal import EntrepriseLegalInfo

logger = logging.getLogger(__name__)

# Optional RapidOCR / pypdfium2 engine for scanned PDFs
try:
    import pypdfium2
    from rapidocr_onnxruntime import RapidOCR
    _ocr_engine = RapidOCR()
except Exception as ocr_init_err:
    logger.warning(f"RapidOCR ou pypdfium2 non initialisé : {ocr_init_err}")
    _ocr_engine = None


def clean_arabic_text(val: Optional[str]) -> str:
    """
    Supprime strictement les caractères arabes et nettoie la ponctuation orpheline
    pour garantir que le document de rapport soit 100% en français / caractères latins.
    """
    if not val or not isinstance(val, str):
        return "Non renseigné"

    # 1. Suppression des plages de caractères arabes
    cleaned = re.sub(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '', val)
    # 2. Nettoyage des parenthèses ou séparateurs orphelins (ex: '()', '( : )', etc.)
    cleaned = re.sub(r'\(\s*[:\-]*\s*\)', '', cleaned)
    # 3. Normalisation des espaces et ponctuation résiduelle
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned).strip(" :-,.\t\r\n")

    return cleaned if len(cleaned) >= 2 else "Non renseigné"


def parse_legal_info_heuristics(text: str) -> Dict[str, Any]:
    """
    Parseur heuristique déterministe haute précision calibré sur les documents officiels marocains :
    1. Registre de Commerce (Modèle 7 - Registre Analytique du Tribunal de Commerce)
    2. Attestation de Régularité Fiscale (DGI - Modèle AAC270B)
    3. Attestation pour soumissionner aux marchés publics (CNSS)
    """
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

    # -------------------------------------------------------------------------
    # 1. ICE (Identifiant Commun de l'Entreprise - 15 chiffres)
    # -------------------------------------------------------------------------
    ice_match = re.search(
        r'\b(?:ICE|I\.?C\.?E\.?|IDENTIFIANT\s+COMMUN)[^\d\n]*?([0-9]{15})\b',
        text,
        re.IGNORECASE
    )
    if ice_match:
        info["ice"] = ice_match.group(1).strip()

    # -------------------------------------------------------------------------
    # 2. Registre de Commerce (RC)
    # -------------------------------------------------------------------------
    rc_match = re.search(
        r'(?:Copie\s+des\s+Inscriptions.*N°\s*:?|Registre\s+du\s+Commerce\s*:?|N°\s*du\s+registre\s+de\s+commerce\s*:?|RC\s*N°\s*:?|N°\s*RC\s*:?)\s*([0-9]{4,10})',
        text,
        re.IGNORECASE
    )
    if rc_match:
        info["rc"] = rc_match.group(1).strip()
    else:
        rc_fallback = re.search(r'\b(?:RC|R\.C\.)\b[^\d\n]*?([0-9]{4,10})', text, re.IGNORECASE)
        if rc_fallback:
            info["rc"] = rc_fallback.group(1).strip()

    # -------------------------------------------------------------------------
    # 3. Identifiant Fiscal (IF - 7 à 9 chiffres sur Attestation DGI ou CNSS)
    # -------------------------------------------------------------------------
    if_match = re.search(
        r'(?:N°\s*d[’\']identification\s+fiscale|Identifiant\s+Fiscal|I\.?F\.?\s*:?)\s*[:\s]*([0-9]{7,9})',
        text,
        re.IGNORECASE
    )
    if if_match:
        info["identifiant_fiscal"] = if_match.group(1).strip()
    else:
        if_fallback = re.search(r'\b(?:IF|I\.F\.)\b[^\d\n]*?([0-9]{7,9})', text, re.IGNORECASE)
        if if_fallback:
            info["identifiant_fiscal"] = if_fallback.group(1).strip()

    # -------------------------------------------------------------------------
    # 4. CNSS (N° d'affiliation - 6 à 10 chiffres sur Attestation CNSS)
    # -------------------------------------------------------------------------
    cnss_match = re.search(
        r'(?:N°\s*d[’\']?aff[li]+iation|Affiliation\s+CNSS|N°\s*CNSS)\s*[:\s]*([0-9]{6,10})',
        text,
        re.IGNORECASE
    )
    if cnss_match:
        info["cnss"] = cnss_match.group(1).strip()
    else:
        # Layout vertical OCR : le numéro précède le libellé sur la ligne au-dessus
        cnss_prev_match = re.search(
            r'([0-9]{6,10})\s*\n\s*N°\s*d[’\']?aff[li]+iation',
            text,
            re.IGNORECASE
        )
        if cnss_prev_match:
            info["cnss"] = cnss_prev_match.group(1).strip()
        else:
            cnss_fallback = re.search(r'\b(?:CNSS|C\.N\.S\.S\.)\b[^\d\n]{0,30}?([0-9]{6,10})', text, re.IGNORECASE)
            if cnss_fallback:
                info["cnss"] = cnss_fallback.group(1).strip()

    # -------------------------------------------------------------------------
    # 5. Forme Juridique
    # -------------------------------------------------------------------------
    if re.search(r'\b(SARL\s*AU|S\.A\.R\.L\s*A\.U|SOCIETE\s+A\s+RESPONSABILITE\s+LIMITEE\s+D\s*[\'’]ASSOCIE\s+UNIQUE)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SARL AU"
    elif re.search(r'\b(SARL|S\.A\.R\.L|SOCIETE\s+A\s+RESPONSABILITE\s+LIMITEE)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SARL"
    elif re.search(r'\b(SA|S\.A\.|SOCIETE\s+ANONYME)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SA"
    elif re.search(r'\b(SAS|S\.A\.S|SOCIETE\s+PAR\s+ACTIONS\s+SIMPLIFIEE)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SAS"
    elif re.search(r'\b(SNC|S\.N\.C)\b', text, re.IGNORECASE):
        info["forme_juridique"] = "SNC"

    # -------------------------------------------------------------------------
    # 6. Date de Création / Immatriculation (JJ/MM/AAAA)
    # -------------------------------------------------------------------------
    date_match = re.search(
        r'(?:Date\s+Immatriculation|Date(?:\s+de)?\s+Cr[eé]ation|Cr[eé][eé]e?\s+le|Date\s+d[’\']affiliation)[^\d\n]*([0-9]{2}[/-][0-9]{2}[/-][0-9]{4})',
        text,
        re.IGNORECASE
    )
    if date_match:
        info["date_creation"] = date_match.group(1).strip()

    # -------------------------------------------------------------------------
    # 7. Nom / Dénomination (Raison sociale en français)
    # -------------------------------------------------------------------------
    denom_match = re.search(
        r'(?:D[eé]nomination|Nom,\s*pr[eé]nom\(s\)\s*ou\s*raison|Nom/Raison\s*Sociale)[^\n:]*:\s*(?:[\u0600-\u06FF\(\)\s]*)\s*([A-Za-z0-9][^\n\r]+?)(?:\s+Sigle|\s*\(|$|\n)',
        text,
        re.IGNORECASE
    )
    if denom_match:
        cleaned_nom = clean_arabic_text(denom_match.group(1))
        if cleaned_nom != "Non renseigné":
            info["nom"] = cleaned_nom

    # -------------------------------------------------------------------------
    # 8. Capital Social (Montant en MAD)
    # -------------------------------------------------------------------------
    cap_match = re.search(
        r'Capital\s+Social[^\d\n]*([0-9\s.,]+)\s*(?:MAD|DH)',
        text,
        re.IGNORECASE
    )
    if cap_match:
        raw_cap = cap_match.group(1).split(",")[0].split(".")[0]
        digits_only = re.sub(r'[^\d]', '', raw_cap)
        if digits_only and int(digits_only) > 0:
            info["capital_social"] = f"{int(digits_only):,}".replace(",", " ")

    # -------------------------------------------------------------------------
    # 9. Adresse du Siège Social (Extraction STRICTE de la version française)
    # -------------------------------------------------------------------------
    addr_found = None

    # Tentative 1 : DGI Attestation ("Domicile fiscal ou siège social" suivi de l'adresse en français sur les lignes suivantes)
    dgi_addr_match = re.search(
        r'Domicile\s+fiscal\s+ou\s+si[eè]ge\s+social[^\n]*\n\s*([A-Za-z0-9][^\n]+(?:\n\s*[A-Za-z0-9][^\n]+){0,2})',
        text,
        re.IGNORECASE
    )
    if dgi_addr_match:
        raw_lines = [l.strip() for l in dgi_addr_match.group(1).split("\n")]
        valid_lines = [l for l in raw_lines if len(l) > 2 and not re.search(r'^(?:Activit|Objet|Cadre|Date|Est\s+en)', l, re.I)]
        if valid_lines:
            cand = clean_arabic_text(" - ".join(valid_lines))
            if cand != "Non renseigné" and len(cand) > 10:
                addr_found = cand

    # Tentative 2 : RC Modèle 7 ("Siège Social (...) : <Adresse>")
    if not addr_found:
        rc_addr_match = re.search(
            r'(?:^|\n)\s*Si[eè]ge\s+Social[^\n:]*:\s*([A-Za-z0-9][^\n]+(?:\n\s*[A-Za-z0-9][^\n]+){0,2})',
            text,
            re.IGNORECASE
        )
        if rc_addr_match:
            raw_lines = [l.strip() for l in rc_addr_match.group(1).split("\n")]
            valid_lines = [l for l in raw_lines if len(l) > 2 and not re.search(r'^(?:Activit|Objet|Cadre|Date|Justificatif|Enseigne)', l, re.I)]
            if valid_lines:
                cand = clean_arabic_text(" ".join(valid_lines))
                if cand != "Non renseigné" and len(cand) > 10:
                    addr_found = cand

    # Tentative 3 : Fallback si non trouvé
    if not addr_found:
        addr_line_match = re.search(
            r'(?:TRITON\s+CENTER[^\n]+|ZONE\s+INDUSTRIELLE[^\n]+|[0-9]+\s*,?\s*(?:BD|BOULEVARD|RUE|AV|AVENUE)[^\n]+)',
            text,
            re.IGNORECASE
        )
        if addr_line_match:
            cand = clean_arabic_text(addr_line_match.group(0))
            if cand != "Non renseigné":
                addr_found = cand

    if addr_found:
        addr_found = re.sub(r'-\s*-+', '-', addr_found)
        addr_found = re.sub(r'\s+', ' ', addr_found).strip(" -")
        info["adresse_siege"] = addr_found

    # -------------------------------------------------------------------------
    # 10. Activité Statutaire & Détaillée (Objet social en français)
    # -------------------------------------------------------------------------
    act_match = re.search(
        r'(?:Activit[eé]\s+effectivement\s+exerc[eé]e|Activit[eé]\s+exerc[eé]e)[^\n:]*:\s*(.+?)(?:\n\s*Si[eè]ge|\n\s*Objet|\n\s*Cadre|\n\s*Est\s+en\s+r[eè]gle|\n\s*Enseigne|$)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if act_match:
        raw_act = act_match.group(1)
        latin_acts = re.findall(r'[A-Za-z0-9\s,°/’\'\.\-#]{6,}', raw_act)
        if latin_acts:
            cleaned_acts = [clean_arabic_text(a) for a in latin_acts if len(a.strip()) > 5]
            valid_acts = [a for a in cleaned_acts if a != "Non renseigné"]
            if valid_acts:
                joined_act = ", ".join(valid_acts[:3])
                info["activite_statutaire"] = joined_act
                info["activite_detaillee"] = joined_act

    # -------------------------------------------------------------------------
    # 11. Associés / Dirigeants & Représentant Légal
    # -------------------------------------------------------------------------
    gerants_matches = re.findall(
        r'([A-Z\s]{3,35})\s*\([^)]*C\.?I\.?N\.?[^)]*\)[,\s]*([A-Z]{3,20})',
        text
    )
    if gerants_matches:
        assoc_list = [f"{m[0].strip()} ({m[1].strip()})" for m in gerants_matches if len(m[0].strip()) > 3]
        if assoc_list:
            info["actionnaires"] = " ; ".join(assoc_list)
            info["representant_legal"] = assoc_list[0]

    return info


class PdfParserService:
    """
    Service dédié à la lecture multi-format et OCR des pièces administratives marocaines
    (RC, Attestation Fiscale, CNSS) et à l'extraction juridique structurée.
    """

    @staticmethod
    def read_pdf_files(file_paths: List[str], dossier_id: int = 0) -> str:
        """
        Extrait le texte des documents PDF.
        Si une page est numérisée (image scannée sans texte numérique),
        bascule automatiquement et silencieusement sur RapidOCR (ONNX).
        """
        combined_text = ""
        for path in file_paths:
            if not path:
                continue

            if not os.path.exists(path):
                logger.warning(f"[{dossier_id}] Fichier introuvable sur le disque : {path}")
                continue

            file_extracted_text = ""
            try:
                # 1. Tentative d'extraction numérique native via pdfplumber
                with pdfplumber.open(path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        # Si la page a très peu de texte (< 50 caractères), c'est très probablement un document scanné
                        if len(page_text.strip()) < 50 and _ocr_engine is not None:
                            try:
                                logger.info(f"[{dossier_id}] Page {i+1} scannée détectée sur {os.path.basename(path)}. Exécution de l'OCR...")
                                doc = pypdfium2.PdfDocument(path)
                                pypdf_page = doc[i]
                                pil_img = pypdf_page.render(scale=2).to_pil()
                                ocr_result, _ = _ocr_engine(pil_img)
                                if ocr_result:
                                    ocr_lines = [line[1] for line in ocr_result]
                                    page_text = "\n".join(ocr_lines)
                                    logger.info(f"[{dossier_id}] OCR terminé avec succès ({len(ocr_lines)} lignes reconnues).")
                            except Exception as ocr_err:
                                logger.warning(f"[{dossier_id}] Échec de l'OCR sur la page {i+1} : {ocr_err}")

                        file_extracted_text += page_text + "\n"

            except Exception as e:
                logger.error(f"[{dossier_id}] Erreur lors de l'ouverture du PDF {path} : {e}")

            combined_text += f"\n=== FICHIER : {os.path.basename(path)} ===\n" + file_extracted_text + "\n"

        return combined_text

    @classmethod
    def extract_legal_info(
        cls,
        file_paths: List[str],
        llm: Optional[Any] = None,
        dossier_id: int = 0
    ) -> Dict[str, Any]:
        """
        Combine l'extraction texte (avec OCR si scanné), le parseur heuristique marocain
        haute précision et le LLM structuré avec consignes strictes anti-arabe.
        """
        combined_text = cls.read_pdf_files(file_paths, dossier_id=dossier_id)
        logger.info(f"[{dossier_id}] {len(combined_text)} caractères extraits des pièces justificatives.")

        # 1. Extraction heuristique déterministe
        heuristics_data = parse_legal_info_heuristics(combined_text)

        # 2. Appel LLM si disponible
        pdf_info = None
        if llm and len(combined_text.strip()) > 30:
            try:
                structured_llm = llm.with_structured_output(EntrepriseLegalInfo)
                prompt = (
                    "Tu es un expert senior en analyse documentaire juridique et fiscale marocaine.\n\n"
                    "DIRECTIVES CRITIQUES DE TRADUCTION & LANGUE :\n"
                    "1. RÈGLE ABSOLUE : Tu DOIS répondre UNIQUEMENT ET STRICTEMENT EN FRANÇAIS.\n"
                    "2. INTERDICTION TOTALE D'ÉCRIRE EN ARABE : Les documents officiels marocains (RC, Attestation Fiscale, CNSS) "
                    "sont bilingues (arabe et français). Tu ne dois JAMAIS reprendre de caractères arabes ni de mentions en arabe.\n"
                    "3. Pour chaque champ (adresse du siège social, dénomination, activités, forme juridique, gérants/actionnaires), "
                    "recherche et extrais SYSTÉMATIQUEMENT la version en français ou la transcription latine figurant dans le document.\n"
                    "4. Ne laisse AUCUN champ vide : si une information n'est absolument pas mentionnée, indique 'Non renseigné'.\n\n"
                    f"Texte intégral des pièces justificatives administratives :\n{combined_text[:12000]}"
                )
                result = structured_llm.invoke(prompt)
                raw_dict = result.model_dump() if hasattr(result, "model_dump") else dict(result)

                # Sanitisation post-LLM : suppression stricte de tout résidu d'arabe
                pdf_info = {}
                for k, v in raw_dict.items():
                    if isinstance(v, str):
                        cleaned = clean_arabic_text(v)
                        pdf_info[k] = cleaned
                    else:
                        pdf_info[k] = v

                logger.info(f"[{dossier_id}] Extraction LLM réussie pour l'entreprise : {pdf_info.get('nom')}")
            except Exception as e:
                logger.warning(f"[{dossier_id}] Erreur lors de l'extraction LLM : {e}. Utilisation du parseur heuristique.")

        if not pdf_info:
            pdf_info = heuristics_data
        else:
            # Réconciliation intelligente : si le LLM a mis 'Non renseigné' mais que les heuristiques ont trouvé,
            # on prend la valeur heuristique !
            for k, v in heuristics_data.items():
                current_val = pdf_info.get(k)
                if current_val in [None, "", "Non renseigné"] and v not in [None, "", "Non renseigné"]:
                    pdf_info[k] = v

        return pdf_info
