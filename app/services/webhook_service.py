import json
import logging
import re
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings
from app.services.pdf_service import clean_arabic_text

logger = logging.getLogger(__name__)

SECTOR_MAPPING = {
    "IND-AUTO": "Industrie Automobile & Composants",
    "IND-AERO": "Industrie Aéronautique & Spatiale",
    "IND-ELEC": "Industrie Électrique & Électronique",
    "AGRO": "Industrie Agroalimentaire & Transformation",
    "TEXTILE": "Textile, Habillement & Confection",
    "CHIMIE": "Industrie Chimique & Parachimique",
    "PHARMA": "Industrie Pharmaceutique & Médicale",
    "METALLURGIE": "Métallurgie, Mécanique & Électromécanique",
    "ENERGIE": "Énergies Renouvelables & Transition Énergétique",
    "DIGITAL": "Technologies de l'Information & Digitalisation",
    "SERVICES": "Services Industriels & Logistique Spécialisée",
    "FabricationMeubles": "Fabrication de Meubles & Industrie du Bois",
}

BANK_MAPPING = {
    "AWB": "Attijariwafa Bank",
    "BP": "Banque Populaire",
    "BOA": "Bank of Africa",
    "BMCE": "Bank of Africa",
    "CDM": "Crédit du Maroc",
    "SG": "Société Générale Maroc",
    "CIH": "CIH Bank",
    "CAM": "Crédit Agricole du Maroc",
    "CFG": "CFG Bank",
    "ALBARID": "Al Barid Bank",
}

LEGAL_MAPPING = {
    "sarlau": "SARL AU",
    "sarl": "SARL",
    "sa": "SA",
    "sas": "SAS",
    "snc": "SNC",
    "personne_physique": "Entreprise Individuelle",
}


def sanitize_all_strings(val: Any) -> Any:
    """Nettoie récursivement tous les champs textes pour éliminer strictement tout caractère arabe."""
    if isinstance(val, dict):
        return {k: sanitize_all_strings(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_all_strings(v) for v in val]
    elif isinstance(val, str):
        cleaned = clean_arabic_text(val)
        return cleaned
    return val


class WebhookService:
    """Service responsible for consolidating the final investment memorandum JSON and notifying Express."""

    @staticmethod
    def build_consolidated_json(
        pdf_info: Dict[str, Any],
        financial_data: Dict[str, Any],
        narratives: Dict[str, Any],
        stepper_data: Optional[Dict[str, Any]] = None,
        test_data: Optional[Dict[str, Any]] = None,
        client_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Formats the unified JSON structure required by Handlebars report generation."""
        stepper_data = stepper_data or {}
        test_data = test_data or {}
        client_info = client_info or {}

        prog_inv = financial_data.get("programme_investissement", {})
        cpc_data = financial_data.get("cpc", {})
        impacts_data = financial_data.get("impacts_socio_economiques", {})
        primes_data = financial_data.get("synthese_primes", {})

        projet_info = financial_data.get("projet", {})
        financement_info = prog_inv.get("financement", {})

        # ---------------------------------------------------------------------
        # 1. Entreprise & Informations Juridiques
        # ---------------------------------------------------------------------
        raw_nom = pdf_info.get("nom")
        if not raw_nom or raw_nom == "Non renseigné":
            raw_nom = client_info.get("nomEntreprise") or test_data.get("nomEntreprise") or "Entreprise Bénéficiaire"

        raw_forme = pdf_info.get("forme_juridique")
        if not raw_forme or raw_forme == "Non renseigné":
            test_forme = str(test_data.get("statutJuridique", "")).lower()
            raw_forme = LEGAL_MAPPING.get(test_forme, "SARL")

        raw_date_crea = pdf_info.get("date_creation")
        if not raw_date_crea or raw_date_crea == "Non renseigné":
            test_annee = test_data.get("anneeCreation")
            raw_date_crea = str(test_annee) if test_annee else "Non renseigné"

        raw_cap = pdf_info.get("capital_social")
        if not raw_cap or raw_cap in ["Non renseigné", "0"]:
            raw_cap = "100 000"

        client_full_name = f"{client_info.get('nom', '')} {client_info.get('prenom', '')}".strip()
        raw_associes = pdf_info.get("actionnaires")
        if not raw_associes or raw_associes == "Non renseigné":
            raw_associes = f"{client_full_name} (Associé Principal)" if client_full_name else "Direction Générale"

        raw_rep = pdf_info.get("representant_legal")
        if not raw_rep or raw_rep == "Non renseigné":
            raw_rep = client_full_name if client_full_name else "Direction Générale"

        raw_adresse = pdf_info.get("adresse_siege")
        if not raw_adresse or raw_adresse == "Non renseigné":
            stepper_addr = stepper_data.get("adresse_projet")
            if stepper_addr and stepper_addr != "N/A":
                raw_adresse = stepper_addr
            else:
                raw_adresse = stepper_data.get("province_id") or "Casablanca"

        # Activité & Branche
        secteur_code = stepper_data.get("secteur_activite") or ""
        test_secteur = test_data.get("secteurTravail") or ""
        human_branche = (
            test_data.get("branche") or
            SECTOR_MAPPING.get(secteur_code) or
            SECTOR_MAPPING.get(test_secteur) or
            (pdf_info.get("branche_activite") if pdf_info.get("branche_activite") != "Non renseigné" else None) or
            "Industrie & Services"
        )

        raw_act_statutaire = pdf_info.get("activite_statutaire")
        if not raw_act_statutaire or raw_act_statutaire == "Non renseigné":
            raw_act_statutaire = SECTOR_MAPPING.get(test_secteur) or test_secteur or "Activités et services industriels"

        raw_act_detaillee = pdf_info.get("activite_detaillee")
        if not raw_act_detaillee or raw_act_detaillee == "Non renseigné":
            raw_act_detaillee = raw_act_statutaire

        # Historique CA (3 exercices)
        ca_history_dict = test_data.get("chiffreAffaires") or {}
        if isinstance(ca_history_dict, str):
            try:
                ca_history_dict = json.loads(ca_history_dict)
            except Exception:
                ca_history_dict = {}

        def format_currency_amount(v: Any) -> str:
            if v in [None, "", "Non renseigné"]:
                return "0"
            try:
                numeric_val = float(str(v).replace(" ", "").replace(",", "."))
                if numeric_val == 0:
                    return "0"
                return f"{int(numeric_val):,}".replace(",", " ")
            except Exception:
                return str(v)

        ca_2023 = format_currency_amount(ca_history_dict.get("chiffreAffaire2023") or ca_history_dict.get("chiffreAffaire2022") or pdf_info.get("ca_2023"))
        ca_2024 = format_currency_amount(ca_history_dict.get("chiffreAffaire2024") or ca_history_dict.get("chiffreAffaire2023") or pdf_info.get("ca_2024"))
        ca_2025 = format_currency_amount(ca_history_dict.get("chiffreAffaire2025") or ca_history_dict.get("chiffreAffaire2024") or pdf_info.get("ca_2025"))

        # ---------------------------------------------------------------------
        # 2. Projet d'Investissement
        # ---------------------------------------------------------------------
        # Mode de financement
        raw_mode = stepper_data.get("mode_financement") or projet_info.get("mode_financement") or financement_info.get("mode_financement")
        if raw_mode == "100_FONDS_PROPRES":
            mode_financement = "100% Fonds Propres"
        elif raw_mode == "DETTE_ET_FP":
            part_fp = stepper_data.get("part_fonds_propres", 30)
            part_dette = 100 - part_fp
            mode_financement = f"Fonds propres ({part_fp}%) et Crédit bancaire ({part_dette}%)"
        elif raw_mode:
            mode_financement = str(raw_mode).replace("_", " ")
        else:
            mode_financement = "Fonds propres (30%) et Crédit bancaire (70%)"

        # Banque partenaire
        raw_banque = stepper_data.get("banque_partenaire") or projet_info.get("banque_partenaire") or "AWB"
        banque_partenaire = BANK_MAPPING.get(raw_banque, raw_banque)

        # Lieu de réalisation & Région
        stepper_addr_proj = stepper_data.get("adresse_projet")
        if stepper_addr_proj and stepper_addr_proj != "N/A":
            lieu_realisation = stepper_addr_proj
        else:
            lieu_realisation = stepper_data.get("province_id") or raw_adresse or "Casablanca"

        region = stepper_data.get("region_id") or test_data.get("region") or projet_info.get("region") or "Casablanca-Settat"

        # Coordonnées GPS
        coordonnees_gps = stepper_data.get("gps_coordinates")
        if not coordonnees_gps or coordonnees_gps == "N/A":
            coordonnees_gps = pdf_info.get("coordonnees_gps") if pdf_info.get("coordonnees_gps") != "Non renseigné" else "33.5731° N, 7.5898° W"

        # Information sur le terrain
        regime_foncier = stepper_data.get("regime_foncier")
        titre_foncier = stepper_data.get("titre_foncier")
        if regime_foncier == "ACQUISITION":
            info_terrain = f"Acquisition en pleine propriété (Titre foncier: {titre_foncier})" if titre_foncier else "Acquisition en pleine propriété"
        elif regime_foncier == "LOCATION":
            info_terrain = f"Bail commercial longue durée (Titre: {titre_foncier})" if titre_foncier else "Bail commercial longue durée"
        elif titre_foncier:
            info_terrain = f"{regime_foncier} (Titre: {titre_foncier})"
        else:
            info_terrain = regime_foncier or projet_info.get("info_terrain") or "Bail commercial longue durée"

        # Activité & Biens/Services
        activite_projet = f"Création et modernisation d'unités de production et services spécialisés en {human_branche}"
        biens_services = f"Prestations et solutions techniques spécialisées en {human_branche}"

        from app.services.consultant_service import VirtualConsultantService
        presentation_projet_text = narratives.get("presentation_projet") or f"Projet d'investissement et de modernisation industrielle TPME - Secteur {human_branche}"
        raw_desc = projet_info.get("description") or presentation_projet_text
        description_projet = VirtualConsultantService.sanitize_plain_text(raw_desc)

        final_projet = {
            "description": description_projet,
            "lieu_realisation": lieu_realisation,
            "region": region,
            "coordonnees_gps": coordonnees_gps,
            "info_terrain": info_terrain,
            "branche_activite": human_branche,
            "activite_projet": activite_projet,
            "biens_services": biens_services,
            "mode_financement": mode_financement,
            "banque_partenaire": banque_partenaire,
        }

        consolidated = {
            "presentation_generale": {
                "type_dossier": "Projet d'Investissement TPME",
                "cabinet": {
                    "nom_court": "Tamkeen"
                },
                "entreprise": {
                    "nom": raw_nom,
                    "ice": pdf_info.get("ice", "Non renseigné"),
                    "rc": pdf_info.get("rc", "Non renseigné"),
                    "forme_juridique": raw_forme,
                    "activite_statutaire": raw_act_statutaire,
                    "date_creation": raw_date_crea,
                    "branche_activite": human_branche,
                    "activite_detaillee": raw_act_detaillee,
                    "capital_social": str(raw_cap),
                    "actionnaires": raw_associes,
                    "identifiant_fiscal": pdf_info.get("identifiant_fiscal", "Non renseigné"),
                    "cnss": pdf_info.get("cnss", "Non renseigné"),
                    "representant_legal": raw_rep,
                    "adresse_siege": raw_adresse,
                    "ca_historique": {
                        "ca_2023": ca_2023,
                        "ca_2024": ca_2024,
                        "ca_2025": ca_2025,
                    }
                },
                "projet": final_projet
            },
            "programme_investissement": prog_inv,
            "cpc": cpc_data,
            "impacts_socio_economiques": impacts_data,
            "synthese_primes": primes_data,
            "narrative_report": narratives,
            "argumentaires": narratives
        }

        # Nettoyage anti-arabe absolu sur tous les champs du rapport
        return sanitize_all_strings(consolidated)

    @classmethod
    def send_webhook(cls, dossier_id: int, final_json: Dict[str, Any]) -> bool:
        """Dispatches the consolidated report to Express webhook endpoint."""
        webhook_url = settings.EXPRESS_WEBHOOK_URL
        payload = {
            "dossierId": dossier_id,
            "result_json": final_json
        }

        headers = {
            "Content-Type": "application/json",
        }
        if settings.INTERNAL_WEBHOOK_SECRET:
            headers["X-Internal-Secret"] = settings.INTERNAL_WEBHOOK_SECRET
            headers["Authorization"] = f"Bearer {settings.INTERNAL_WEBHOOK_SECRET}"

        try:
            response = httpx.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=settings.WEBHOOK_TIMEOUT_SECONDS
            )
            logger.info(f"[{dossier_id}] Webhook envoyé à {webhook_url}. Code: {response.status_code}")
            return response.status_code in [200, 201, 202, 204]
        except Exception as e:
            logger.error(f"[{dossier_id}] Erreur lors de l'envoi du webhook à {webhook_url}: {e}")
            return False
