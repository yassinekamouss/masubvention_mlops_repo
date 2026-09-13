import logging
from typing import Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebhookService:
    """Service responsible for consolidating the final investment memorandum JSON and notifying Express."""

    @staticmethod
    def build_consolidated_json(
        pdf_info: Dict[str, Any],
        financial_data: Dict[str, Any],
        narratives: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Formats the unified JSON structure required by Handlebars report generation."""
        prog_inv = financial_data.get("programme_investissement", {})
        cpc_data = financial_data.get("cpc", {})
        impacts_data = financial_data.get("impacts_socio_economiques", {})
        primes_data = financial_data.get("synthese_primes", {})

        projet_info = financial_data.get("projet", {})
        financement_info = prog_inv.get("financement", {})
        mode_financement = (
            projet_info.get("mode_financement") or
            financement_info.get("mode_financement") or
            "Fonds propres (30%) et Crédit bancaire (70%)"
        )

        presentation_projet_text = narratives.get("presentation_projet") or "Projet d'investissement et de modernisation industrielle TPME"
        description_projet = projet_info.get("description") or presentation_projet_text
        lieu_realisation = projet_info.get("lieu_realisation") or pdf_info.get("adresse_siege") or "Casablanca"
        region = projet_info.get("region") or "Casablanca-Settat"
        coordonnees_gps = (
            pdf_info.get("coordonnees_gps")
            if pdf_info.get("coordonnees_gps") and pdf_info.get("coordonnees_gps") != "Non renseigné"
            else (projet_info.get("coordonnees_gps") or "33.5731° N, 7.5898° W")
        )
        info_terrain = projet_info.get("info_terrain") or "Bail commercial longue durée"
        branche_activite = (
            pdf_info.get("branche_activite_projet")
            if pdf_info.get("branche_activite_projet") and pdf_info.get("branche_activite_projet") != "Non renseigné"
            else (pdf_info.get("branche_activite") or projet_info.get("branche_activite") or "Industrie & Services")
        )
        activite_projet = projet_info.get("activite_projet") or pdf_info.get("activite_detaillee") or "Développement et modernisation des capacités industrielles"
        biens_services = (
            pdf_info.get("biens_services")
            if pdf_info.get("biens_services") and pdf_info.get("biens_services") != "Non renseigné"
            else (projet_info.get("biens_services") or "Prestations industrielles et services associés")
        )
        banque_partenaire = projet_info.get("banque_partenaire") or "Attijariwafa Bank"

        final_projet = {
            "description": description_projet,
            "lieu_realisation": lieu_realisation,
            "region": region,
            "coordonnees_gps": coordonnees_gps,
            "info_terrain": info_terrain,
            "branche_activite": branche_activite,
            "activite_projet": activite_projet,
            "biens_services": biens_services,
            "mode_financement": mode_financement,
            "banque_partenaire": banque_partenaire,
        }

        return {
            "presentation_generale": {
                "type_dossier": "Projet d'Investissement TPME",
                "cabinet": {
                    "nom_court": "Tamkeen"
                },
                "entreprise": {
                    "nom": pdf_info.get("nom", "Non renseigné"),
                    "ice": pdf_info.get("ice", "Non renseigné"),
                    "rc": pdf_info.get("rc", "Non renseigné"),
                    "forme_juridique": pdf_info.get("forme_juridique", "Non renseigné"),
                    "activite_statutaire": pdf_info.get("activite_statutaire", "Non renseigné"),
                    "date_creation": pdf_info.get("date_creation", "Non renseigné"),
                    "branche_activite": pdf_info.get("branche_activite", "Non renseigné"),
                    "activite_detaillee": pdf_info.get("activite_detaillee", "Non renseigné"),
                    "capital_social": str(pdf_info.get("capital_social", "Non renseigné")),
                    "actionnaires": pdf_info.get("actionnaires", "Non renseigné"),
                    "identifiant_fiscal": pdf_info.get("identifiant_fiscal", "Non renseigné"),
                    "cnss": pdf_info.get("cnss", "Non renseigné"),
                    "representant_legal": pdf_info.get("representant_legal", "Non renseigné"),
                    "adresse_siege": pdf_info.get("adresse_siege", "Non renseigné"),
                    "ca_historique": {
                        "ca_2023": str(pdf_info.get("ca_2023", "0")),
                        "ca_2024": str(pdf_info.get("ca_2024", "0")),
                        "ca_2025": str(pdf_info.get("ca_2025", "0")),
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

    @classmethod
    def send_webhook(cls, dossier_id: int, final_json: Dict[str, Any]) -> bool:
        """Dispatches the consolidated report to Express webhook endpoint."""
        webhook_url = settings.EXPRESS_WEBHOOK_URL
        payload = {
            "dossierId": dossier_id,
            "result_json": final_json
        }

        try:
            response = httpx.post(
                webhook_url,
                json=payload,
                timeout=settings.WEBHOOK_TIMEOUT_SECONDS
            )
            logger.info(f"[{dossier_id}] Webhook envoyé à {webhook_url}. Code: {response.status_code}")
            return response.status_code in [200, 201, 202, 204]
        except Exception as e:
            logger.error(f"[{dossier_id}] Erreur lors de l'envoi du webhook à {webhook_url}: {e}")
            return False
