import logging
from typing import Dict, Any, Optional
from app.schemas.narrative import NarrativeReport

logger = logging.getLogger(__name__)


class VirtualConsultantService:
    """Service acting as the Senior Investment Consultant for Moroccan Charter Dossiers."""

    @classmethod
    def generate_narratives(
        cls,
        pdf_info: Dict[str, Any],
        financial_data: Dict[str, Any],
        llm: Optional[Any] = None,
        dossier_id: int = 0
    ) -> Dict[str, str]:
        """Generates the 4 strategic investment memorandum sections using LLM or deterministic expert rules."""
        company_name = pdf_info.get("nom") if pdf_info.get("nom") != "Non renseigné" else "L'Entreprise"
        forme_juridique = pdf_info.get("forme_juridique") if pdf_info.get("forme_juridique") != "Non renseigné" else "SARL"
        secteur = pdf_info.get("branche_activite") if pdf_info.get("branche_activite") != "Non renseigné" else "Industrie & Services"

        programme_inv = financial_data.get("programme_investissement", {})
        total_capex = programme_inv.get("total_mad") or 0
        financement = programme_inv.get("financement", {})
        part_fp = financement.get("part_fonds_propres", 30)
        part_dette = financement.get("part_dette", 70)

        impacts = financial_data.get("impacts_socio_economiques", {})
        emplois_directs = impacts.get("emplois_directs", 15)
        emplois_indirects = impacts.get("emplois_indirects", 30)

        primes = financial_data.get("synthese_primes", {})
        zone = primes.get("zone", "ZONE_A")
        taux_terri = primes.get("taux_territoriale", 10)
        taux_sect = primes.get("taux_sectorielle", 0)
        bonus_eco = primes.get("bonus_ecologique", 0)
        taux_global = primes.get("taux_global", 15)
        subvention_estimee = primes.get("montant_subvention_estime", 0)

        cpc = financial_data.get("cpc", {})
        ca_dict = cpc.get("ca", {})
        ca_vals = [
            float(v) for v in ca_dict.values()
            if isinstance(v, (int, float, str)) and str(v).replace('.', '', 1).isdigit()
        ]
        ca_croisiere = max(ca_vals) if ca_vals else 2500

        projet_dict = financial_data.get("projet", {})
        region = projet_dict.get("region") or "Casablanca-Settat"
        lieu = projet_dict.get("lieu_realisation") or "Zone Industrielle"

        narratives = None
        if llm:
            try:
                structured_llm = llm.with_structured_output(NarrativeReport)
                prompt = f"""
Tu es un Consultant Senior Spécialiste de la Charte de l'Investissement Marocaine (Loi-cadre n° 03-22) et du Financement des TPME au sein du cabinet Tamkeen.
Ton objectif est de rédiger un dossier d'argumentation d'investissement irréprochable et hautement convaincant pour la Commission Régionale Unifiée d'Investissement (CRUI) et les partenaires bancaires.

Informations sur l'entreprise :
- Raison sociale : {company_name} ({forme_juridique})
- Secteur d'activité : {secteur}
- Implantation : {lieu} ({region}) - {zone}
- Activité statutaire / détaillée : {pdf_info.get('activite_statutaire', 'Non renseigné')}

Données financières déterministes validées :
- Montant total du programme d'investissement : {total_capex} MAD
- Financement : {part_fp}% Fonds propres / {part_dette}% Crédit bancaire
- Prime territoriale : {taux_terri}% ({zone})
- Prime sectorielle : {taux_sect}%
- Bonus écologique : {bonus_eco}%
- Taux global de subvention : {taux_global}% (Subvention estimée : {subvention_estimee} MAD)
- Chiffre d'affaires à maturité : {ca_croisiere} KMAD
- Emplois directs stables à créer : {emplois_directs}
- Emplois indirects : {emplois_indirects}

Rédige les 4 sections obligatoires suivantes avec une haute exigence de rigueur économique et financière :
1. `presentation_projet` : Synthèse de l'opportunité d'investissement, modèle économique, pertinence technologique et alignement avec la Charte de l'Investissement.
2. `coherence_territoriale` : Justification de l'implantation dans la région {region}, intégration dans l'écosystème territorial et conformité avec les critères de la prime territoriale ({zone}).
3. `impact_socio_economique_argumentaire` : Valorisation de la création d'emplois ({emplois_directs} directs), montée en compétences, inclusion/parité et contribution à la transition écologique.
4. `viabilite_financiere` : Démonstration de la solidité financière, rentabilité d'exploitation, capacité d'autofinancement et maîtrise du ratio dette/fonds propres.
"""
                result = structured_llm.invoke(prompt)
                narratives = result.model_dump() if hasattr(result, 'model_dump') else dict(result)
                logger.info(f"[{dossier_id}] Argumentaires générés via LLM avec succès.")
            except Exception as e:
                logger.warning(f"[{dossier_id}] Erreur LLM Consultant Virtuel: {e}. Bascule sur le générateur déterministe.")

        # Fallback expert déterministe
        if not narratives or not all(narratives.get(k) for k in [
            "presentation_projet", "coherence_territoriale", "impact_socio_economique_argumentaire", "viabilite_financiere"
        ]):
            narratives = cls.generate_expert_deterministic_narrative(
                company_name=company_name,
                forme_juridique=forme_juridique,
                secteur=secteur,
                total_capex=total_capex,
                part_fp=part_fp,
                part_dette=part_dette,
                taux_terri=taux_terri,
                zone=zone,
                bonus_eco=bonus_eco,
                taux_global=taux_global,
                subvention_estimee=subvention_estimee,
                ca_croisiere=ca_croisiere,
                emplois_directs=emplois_directs,
                emplois_indirects=emplois_indirects,
                region=region,
            )

        return narratives

    @staticmethod
    def generate_expert_deterministic_narrative(
        company_name: str,
        forme_juridique: str,
        secteur: str,
        total_capex: float,
        part_fp: float,
        part_dette: float,
        taux_terri: float,
        zone: str,
        bonus_eco: float,
        taux_global: float,
        subvention_estimee: float,
        ca_croisiere: float,
        emplois_directs: int,
        emplois_indirects: int,
        region: str,
    ) -> Dict[str, str]:
        """High-grade economic narrative calibrated to Moroccan Investment Charter criteria."""
        capex_str = f"{total_capex:,.0f}".replace(",", " ") if isinstance(total_capex, (int, float)) and total_capex > 0 else "de premier plan"
        subv_str = f"{subvention_estimee:,.0f}".replace(",", " ") if isinstance(subvention_estimee, (int, float)) and subvention_estimee > 0 else "substantielle"
        zone_label = "Zone A (Province dynamique)" if zone == "ZONE_A" else "Zone B (Province prioritaire à fort potentiel de rattrapage)"

        return {
            "presentation_projet": (
                f"Le présent programme d'investissement porté par la société {company_name} ({forme_juridique}), "
                f"opérant dans la branche '{secteur}', concrétise une étape majeure de son développement industriel et commercial. "
                f"Doté d'une enveloppe globale de {capex_str} MAD, ce projet structurant vise à moderniser les installations techniques, "
                f"élargir la gamme de services et de biens produits à haute valeur ajoutée, et intégrer des technologies de pointe "
                f"pour répondre aux normes internationales les plus exigeantes. Ce programme s'inscrit en parfaite harmonie avec "
                f"les objectifs stratégiques de la nouvelle Charte de l'Investissement marocaine (Loi-cadre n° 03-22), favorisant "
                f"l'essor de TPME pérennes, compétitives et résilientes sur les marchés national et régional."
            ),
            "coherence_territoriale": (
                f"Le choix d'implantation du projet au sein de la région {region} ({zone_label}) répond à une logique "
                f"d'intégration économique territoriale optimale. La proximité des infrastructures autoroutières, aéroportuaires "
                f"et des zones d'activités logistiques de la région assure une connectivité fluide avec les donneurs d'ordres "
                f"et les circuits de distribution. En s'insérant activement dans le tissu productif local, le projet bénéficie de la "
                f"prime territoriale fixée à {taux_terri}%, concourant directement au rééquilibrage spatial et à la dynamisation des "
                f"bassins d'emploi de la province conformément aux orientations des Schémas Régionaux d'Aménagement du Territoire (SRAT)."
            ),
            "impact_socio_economique_argumentaire": (
                f"L'impact socio-économique du projet est hautement qualitatif et créateur de valeur partagée. Le programme garantit "
                f"la création ferme de {emplois_directs} emplois directs stables et permanents ainsi que {emplois_indirects} emplois "
                f"indirects liés à la chaîne de sous-traitance et de maintenance locale. L'entreprise s'engage formellement dans une politique "
                f"RH inclusive privilégiant l'insertion des jeunes diplômés, la formation technique continue et une cible de parité "
                f"femmes-hommes d'au moins 40% sur les postes techniques et d'encadrement. De surcroît, le projet intègre des dispositifs "
                f"d'efficacité énergétique et d'écoconception (éligibles au bonus durable de {bonus_eco}%), attestant d'une démarche responsable "
                f"et décarbonée exemplaire."
            ),
            "viabilite_financiere": (
                f"L'analyse prévisionnelle démontre la viabilité et l'équilibre financier rigoureux de l'opération. L'investissement de "
                f"{capex_str} MAD est financé de manière saine et prudente avec {part_fp}% d'apport en fonds propres et {part_dette}% par dette "
                f"bancaire à moyen/long terme, garantissant un ratio de levier financier maîtrisé. L'optimisation du plan de financement par le "
                f"dispositif de soutien aux TPME permet de mobiliser un soutien public estimé à {subv_str} MAD ({taux_global}% du CAPEX éligible). "
                f"Les flux d'exploitation projetés sur 6 ans confirment une rentabilité robuste avec un chiffre d'affaires atteignant {ca_croisiere:,.0f} KMAD, "
                f"dégageant une marge d'exploitation résiliente et une capacité d'autofinancement (CAF) largement suffisante pour honorer "
                f"le service de la dette bancaire tout en préservant le fonds de roulement."
            ),
        }
