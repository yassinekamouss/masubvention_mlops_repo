import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure masubvention_mlops is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Modular imports
from app import create_app
from app.core import settings, LLMFactory
from app.schemas import (
    ExtractionFiles,
    ExtractionRequest,
    EntrepriseLegalInfo,
    NarrativeReport,
)
from app.services import (
    PdfParserService,
    parse_legal_info_heuristics,
    VirtualConsultantService,
    WebhookService,
)
from app.workflow import (
    workflow_graph,
    process_dossier_task,
)

# Backward-compatible main import
import main


class TestMLOpsPipeline(unittest.TestCase):

    def setUp(self):
        self.mock_financial_data = {
            "programme_investissement": {
                "total_mad": 1500000.0,
                "rubriques": {
                    "frais_etudes": 50000.0,
                    "foncier_prive": 0.0,
                    "foncier_loyer": 200000.0,
                    "infrastructures": 0.0,
                    "amenagements": 250000.0,
                    "equipements": 1000000.0,
                    "autres": 0.0,
                },
                "planning": {
                    "frais_etudes": {"2026": 50000.0, "2027": 0.0, "2028": 0.0},
                    "bien_immeuble": {"2026": 200000.0, "2027": 0.0, "2028": 0.0},
                    "amenagements": {"2026": 150000.0, "2027": 100000.0, "2028": 0.0},
                    "equipements": {"2026": 500000.0, "2027": 300000.0, "2028": 200000.0},
                    "total": {"2026": 900000.0, "2027": 400000.0, "2028": 200000.0},
                },
                "financement": {
                    "mode_financement": "Fonds propres (35%) et Crédit bancaire (65%)",
                    "total_capex": 1500000.0,
                    "montant_dette": 975000.0,
                    "apport_fonds_propres": 525000.0,
                    "part_fonds_propres": 35.0,
                    "part_dette": 65.0,
                },
            },
            "cpc": {
                "ventes": {"2026": 1200, "2027": 1800, "2028": 2400, "2029": 3000, "2030": 3500, "2031": 4000},
                "ca": {"2026": 1200, "2027": 1800, "2028": 2400, "2029": 3000, "2030": 3500, "2031": 4000},
                "achats": {"2026": 300, "2027": 450, "2028": 600, "2029": 750, "2030": 875, "2031": 1000},
                "charges_externes": {"2026": 150, "2027": 180, "2028": 200, "2029": 220, "2030": 240, "2031": 260},
                "personnel": {"2026": 350, "2027": 420, "2028": 500, "2029": 580, "2030": 650, "2031": 700},
                "dotations_exploitation": {"2026": 250, "2027": 250, "2028": 250, "2029": 250, "2030": 250, "2031": 0},
                "total_charges_exploitation": {"2026": 1050, "2027": 1300, "2028": 1550, "2029": 1800, "2030": 2015, "2031": 1960},
                "resultat_exploitation": {"2026": 150, "2027": 500, "2028": 850, "2029": 1200, "2030": 1485, "2031": 2040},
                "resultat_courant": {"2026": 100, "2027": 460, "2028": 820, "2029": 1180, "2030": 1475, "2031": 2040},
                "resultat_avant_impots": {"2026": 100, "2027": 460, "2028": 820, "2029": 1180, "2030": 1475, "2031": 2040},
                "impots_resultats": {"2026": 20, "2027": 92, "2028": 164, "2029": 236, "2030": 295, "2031": 408},
                "resultat_net": {"2026": 80, "2027": 368, "2028": 656, "2029": 944, "2030": 1180, "2031": 1632},
            },
            "impacts_socio_economiques": {
                "emplois_directs": 18,
                "emplois_indirects": 36,
                "role_regional": "Création de 18 emplois directs qualifiés en région Casablanca-Settat.",
                "role_balance_commerciale": "Substitution aux importations d'analyses et de tests de laboratoire.",
                "ca_global": {"2026": 1200, "2027": 1800, "2028": 2400, "2029": 3000, "2030": 3500, "2031": 4000, "total": 15900},
                "ca_lie": {"2026": 800, "2027": 1300, "2028": 1900, "2029": 2500, "2030": 3000, "2031": 3500, "total": 13000},
                "va_globale": {"2026": 750, "2027": 1170, "2028": 1600, "2029": 2030, "2030": 2385, "2031": 2740, "total": 10675},
                "va_liee": {"2026": 500, "2027": 850, "2028": 1270, "2029": 1690, "2030": 2045, "2031": 2400, "total": 8755},
                "directs": {"2026": 8, "2027": 6, "2028": 4, "2029": 0, "2030": 0, "2031": 0, "total": 18},
                "indirects": {"2026": 16, "2027": 12, "2028": 8, "2029": 0, "2030": 0, "2031": 0, "total": 36},
                "effectif_cumule": {"2026": 8, "2027": 14, "2028": 18, "2029": 18, "2030": 18, "2031": 18, "total": 18},
            },
            "synthese_primes": {
                "zone": "ZONE_A",
                "taux_territoriale": 10.0,
                "taux_sectorielle": 5.0,
                "bonus_ecologique": 3.0,
                "taux_global": 18.0,
                "total_capex_ht": 1500000.0,
                "montant_subvention_estime": 270000.0,
            },
            "projet": {
                "description": "Création d'un laboratoire moderne d'analyses industrielles et environnementales",
                "lieu_realisation": "Nouaceur, Casablanca",
                "region": "Casablanca-Settat",
                "coordonnees_gps": "33.3642° N, 7.5898° W",
                "info_terrain": "Bail commercial longue durée (Zone Industrielle Midparc)",
                "branche_activite": "Industrie & Services Technologiques",
                "activite_projet": "Prestations de contrôle analytique et métrologie de pointe",
                "biens_services": "Analyses physico-chimiques, métrologie et audits de conformité",
                "mode_financement": "Fonds propres (35%) et Crédit bancaire (65%)",
                "banque_partenaire": "Attijariwafa Bank",
            }
        }

    def test_schemas_validation(self):
        """Vérifie la validité des modèles Pydantic."""
        files = ExtractionFiles(
            file_fiscale="/tmp/fiscale.pdf",
            file_rc="/tmp/rc.pdf",
            file_cnss="/tmp/cnss.pdf"
        )
        self.assertEqual(files.file_fiscale, "/tmp/fiscale.pdf")

        req = ExtractionRequest(
            dossierId=42,
            files=files,
            financial_data=self.mock_financial_data
        )
        self.assertEqual(req.dossierId, 42)
        self.assertIn("programme_investissement", req.financial_data)

    def test_heuristics_parser(self):
        """Vérifie l'extraction regex de l'identité légale de l'entreprise via PdfParserService."""
        mock_doc = """
        ROYAUME DU MAROC - TRIBUNAL DE COMMERCE DE CASABLANCA
        REGISTRE DU COMMERCE : 458921
        IDENTIFIANT COMMUN DE L'ENTREPRISE (ICE) : 002345678000092
        IDENTIFIANT FISCAL (IF) : 56789012
        NUMERO D'AFFILIATION CNSS : 987654321
        DENOMINATION : TECHNO-LAB MAROC SARL AU
        FORME JURIDIQUE : SARL AU
        CAPITAL SOCIAL : 500 000 DH
        DATE DE CREATION : 15/04/2021
        SIEGE SOCIAL : 45 Boulevard Abdelmoumen, Casablanca
        """
        extracted = parse_legal_info_heuristics(mock_doc)
        self.assertEqual(extracted["ice"], "002345678000092")
        self.assertEqual(extracted["rc"], "458921")
        self.assertEqual(extracted["identifiant_fiscal"], "56789012")
        self.assertEqual(extracted["cnss"], "987654321")
        self.assertIn("SARL", extracted["forme_juridique"])
        self.assertIn("TECHNO-LAB MAROC", extracted["nom"])

    def test_virtual_consultant_service_expert_narrative(self):
        """Vérifie la génération déterministe d'argumentaires experts sans LLM."""
        narratives = VirtualConsultantService.generate_expert_deterministic_narrative(
            company_name="TECHNO-LAB MAROC",
            forme_juridique="SARL AU",
            secteur="Industrie & Services Technologiques",
            total_capex=1500000.0,
            part_fp=35.0,
            part_dette=65.0,
            taux_terri=10.0,
            zone="ZONE_A",
            bonus_eco=3.0,
            taux_global=18.0,
            subvention_estimee=270000.0,
            ca_croisiere=4000.0,
            emplois_directs=18,
            emplois_indirects=36,
            region="Casablanca-Settat",
        )
        self.assertIn("presentation_projet", narratives)
        self.assertIn("coherence_territoriale", narratives)
        self.assertIn("impact_socio_economique_argumentaire", narratives)
        self.assertIn("viabilite_financiere", narratives)
        self.assertIn("1 500 000 MAD", narratives["presentation_projet"])
        self.assertIn("Casablanca-Settat", narratives["coherence_territoriale"])
        self.assertIn("18 emplois directs", narratives["impact_socio_economique_argumentaire"])
        self.assertIn("270 000 MAD", narratives["viabilite_financiere"])

    def test_webhook_service_build_json(self):
        """Vérifie la consolidation du JSON final pour Handlebars."""
        mock_pdf_info = {
            "nom": "TEST COMPANY",
            "ice": "0011223344",
            "rc": "123456",
            "forme_juridique": "SARL",
            "adresse_siege": "Casablanca",
        }
        mock_narratives = {
            "presentation_projet": "Projet test",
            "coherence_territoriale": "Territoire test",
            "impact_socio_economique_argumentaire": "Impact test",
            "viabilite_financiere": "Viabilité test",
        }
        final_json = WebhookService.build_consolidated_json(
            pdf_info=mock_pdf_info,
            financial_data=self.mock_financial_data,
            narratives=mock_narratives
        )
        self.assertIn("presentation_generale", final_json)
        self.assertEqual(final_json["presentation_generale"]["entreprise"]["nom"], "TEST COMPANY")
        self.assertEqual(final_json["presentation_generale"]["projet"]["region"], "Casablanca-Settat")
        self.assertEqual(final_json["programme_investissement"]["total_mad"], 1500000.0)

    def test_llm_factory_safety(self):
        """Vérifie que la factory LLM ne crash pas si aucune clé API n'est fournie."""
        # Sans clé API valide, retourne None ou instance configurée en toute sécurité
        llm = LLMFactory.get_llm()
        # Doit être soit None, soit une instance valide
        self.assertTrue(llm is None or hasattr(llm, "invoke"))

    def test_graph_structure_and_execution(self):
        """Vérifie l'exécution complète du graphe LangGraph (extract_pdf -> virtual_consultant -> consolidate_webhook)."""
        node_keys = list(workflow_graph.nodes.keys())
        self.assertIn("extract_pdf_llm", node_keys)
        self.assertIn("virtual_consultant", node_keys)
        self.assertIn("consolidate_webhook", node_keys)
        self.assertNotIn("extract_excel", node_keys)

        initial_state = {
            "dossier_id": 99,
            "file_paths": {
                "file_fiscale": "",
                "file_rc": "",
                "file_cnss": ""
            },
            "financial_data": self.mock_financial_data,
            "pdf_extracted_info": {},
            "narrative_report": {},
            "final_json": {}
        }

        output = workflow_graph.invoke(initial_state)

        narratives = output.get("narrative_report", {})
        self.assertIn("presentation_projet", narratives)
        self.assertIn("coherence_territoriale", narratives)
        self.assertIn("impact_socio_economique_argumentaire", narratives)
        self.assertIn("viabilite_financiere", narratives)

        final_json = output.get("final_json", {})
        self.assertIn("presentation_generale", final_json)
        self.assertIn("programme_investissement", final_json)
        self.assertIn("cpc", final_json)
        self.assertIn("impacts_socio_economiques", final_json)
        self.assertIn("synthese_primes", final_json)

    def test_fastapi_endpoints(self):
        """Vérifie l'API FastAPI et les endpoints /health et /api/v1/extract."""
        client = TestClient(main.app)

        # Healthcheck
        res_health = client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json().get("status"), "ok")

        # Extract
        payload = {
            "dossierId": 123,
            "files": {
                "file_fiscale": "/tmp/test_fiscale.pdf",
                "file_rc": "/tmp/test_rc.pdf",
                "file_cnss": "/tmp/test_cnss.pdf"
            },
            "financial_data": self.mock_financial_data
        }
        res_extract = client.post("/api/v1/extract", json=payload)
        self.assertEqual(res_extract.status_code, 200)
        self.assertEqual(res_extract.json()["status"], "processing")
        self.assertIn("Dossier 123 received", res_extract.json()["message"])


if __name__ == "__main__":
    unittest.main()
