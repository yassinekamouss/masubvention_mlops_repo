import logging
from typing import Dict, Any, Optional
from app.schemas.narrative import NarrativeReport
from app.services.pdf_service import clean_arabic_text

logger = logging.getLogger(__name__)


class VirtualConsultantService:
    """Service acting as the Senior Investment Consultant for Moroccan Charter Dossiers."""

    @classmethod
    def generate_narratives(
        cls,
        pdf_info: Dict[str, Any],
        financial_data: Dict[str, Any],
        stepper_data: Optional[Dict[str, Any]] = None,
        test_data: Optional[Dict[str, Any]] = None,
        client_info: Optional[Dict[str, Any]] = None,
        llm: Optional[Any] = None,
        dossier_id: int = 0
    ) -> Dict[str, str]:
        """Generates the 4 strategic investment memorandum sections using LLM or deterministic expert rules."""
        stepper_data = stepper_data or {}
        test_data = test_data or {}
        client_info = client_info or {}

        company_name = (
            pdf_info.get("nom")
            if pdf_info.get("nom") and pdf_info.get("nom") != "Non renseigné"
            else (client_info.get("nomEntreprise") or test_data.get("nomEntreprise") or "L'Entreprise")
        )
        forme_juridique = (
            pdf_info.get("forme_juridique")
            if pdf_info.get("forme_juridique") and pdf_info.get("forme_juridique") != "Non renseigné"
            else (str(test_data.get("statutJuridique", "SARL")).upper())
        )
        secteur = (
            test_data.get("branche") or
            test_data.get("secteurTravail") or
            (pdf_info.get("branche_activite") if pdf_info.get("branche_activite") != "Non renseigné" else None) or
            "Industrie & Services"
        )

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

        def _to_pct(val, default):
            try:
                f = float(val)
                return round(f * 100, 1) if 0 < f <= 1 else round(f, 1)
            except Exception:
                return default

        taux_terri = _to_pct(primes.get("taux_territoriale"), 10.0)
        taux_sect = _to_pct(primes.get("taux_sectorielle") or primes.get("taux_emploi"), 0.0)
        bonus_eco = _to_pct(primes.get("bonus_ecologique") or primes.get("taux_prioritaire"), 0.0)
        taux_global = _to_pct(primes.get("taux_global"), 15.0)
        subvention_estimee = primes.get("montant_subvention_estime", 0)

        cpc = financial_data.get("cpc", {})
        ca_dict = cpc.get("ca", {})
        ca_vals = [
            float(v) for v in ca_dict.values()
            if isinstance(v, (int, float, str)) and str(v).replace('.', '', 1).isdigit()
        ]
        ca_croisiere = max(ca_vals) if ca_vals else 2500

        projet_dict = financial_data.get("projet", {})
        region = stepper_data.get("region_id") or test_data.get("region") or projet_dict.get("region") or "Casablanca-Settat"
        lieu = stepper_data.get("adresse_projet") or stepper_data.get("province_id") or projet_dict.get("lieu_realisation") or "Zone Industrielle"

        total_capex_fmt = f"{total_capex:,.0f}".replace(",", " ") if isinstance(total_capex, (int, float)) and total_capex > 0 else "de premier plan"
        subv_fmt = f"{subvention_estimee:,.0f}".replace(",", " ") if isinstance(subvention_estimee, (int, float)) and subvention_estimee > 0 else "substantielle"

        narratives = None
        if llm:
            try:
                structured_llm = llm.with_structured_output(NarrativeReport)
                prompt = f"""
Tu es un Consultant Senior Spécialiste de la Charte de l'Investissement Marocaine (Loi-cadre n° 03-22) et du Financement des TPME au sein du cabinet Tamkeen.
Ton objectif est de rédiger un dossier d'argumentation d'investissement irréprochable et hautement convaincant pour la Commission Régionale Unifiée d'Investissement (CRUI) et les partenaires bancaires.

Informations sur l'entreprise :
- Raison sociale : {company_name} ({forme_juridique})
- Secteur / Métier : {secteur}
- Implantation : {lieu} ({region}) - {zone}
- Activité statutaire / détaillée : {pdf_info.get('activite_statutaire', 'Non renseigné')}

Données financières déterministes validées :
- Montant total du programme d'investissement : {total_capex_fmt} MAD
- Financement : {part_fp}% Fonds propres / {part_dette}% Crédit bancaire
- Prime territoriale : {taux_terri}% ({zone})
- Prime sectorielle : {taux_sect}%
- Bonus prioritaire / transition écologique : {bonus_eco}%
- Taux global de subvention : {taux_global}% (Subvention estimée : {subv_fmt} MAD)
- Chiffre d'affaires à maturité : {ca_croisiere:,.0f} KMAD
- Emplois directs stables à créer : {emplois_directs}
- Emplois indirects : {emplois_indirects}

DIRECTIVES IMPÉRATIVES DE STYLE ET DE FORME :
1. Rédige chaque section sous forme de 1 à 2 paragraphes continus de prose professionnelle, fluide et élégante.
2. INTERDICTION FORMELLE d'utiliser de la syntaxe Markdown : AUCUN titre (#, ##, ###), AUCUNE astérisque pour le gras (** ou *), AUCUNE puce de liste (-, *), et ABSOLUMENT AUCUN tableau Markdown (|---|).
3. INTERDICTION d'ajouter des en-têtes généraux du type "DOSSIER D'ARGUMENTATION", "Soumis à la CRUI", ou des sous-titres numérotés ("1.1", "1.2"). Entre directement dans le vif du sujet.
4. Les pourcentages doivent obligatoirement reprendre les vraies valeurs ci-dessus ({taux_global}% de subvention globale, {taux_terri}% de prime territoriale). N'écris jamais 0,2% ou 0,1%.

Rédige les 4 sections obligatoires suivantes :
1. `presentation_projet` : Synthèse concise de l'opportunité d'investissement, modèle économique, pertinence technologique et alignement avec la Charte de l'Investissement.
2. `coherence_territoriale` : Justification de l'implantation dans la région {region}, intégration dans l'écosystème territorial et valorisation de la prime territoriale ({zone} à {taux_terri}%).
3. `impact_socio_economique_argumentaire` : Valorisation de la création de {emplois_directs} emplois directs stables, montée en compétences et politique d'inclusion/durabilité.
4. `viabilite_financiere` : Démonstration de la solidité du montage ({part_fp}% fonds propres, {part_dette}% crédit bancaire), rentabilité d'exploitation et capacité de remboursement.
"""
                result = structured_llm.invoke(prompt)
                raw_dict = result.model_dump() if hasattr(result, 'model_dump') else dict(result)
                # Assainissement anti-markdown strict sur chaque section
                narratives = {
                    k: cls.sanitize_plain_text(raw_dict.get(k, ""))
                    for k in ["presentation_projet", "coherence_territoriale", "impact_socio_economique_argumentaire", "viabilite_financiere"]
                }
                logger.info(f"[{dossier_id}] Argumentaires générés via LLM et assainis avec succès.")
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

    @staticmethod
    def sanitize_plain_text(text: str) -> str:
        """Strips raw markdown syntax (asterisks, pipes, headers, preamble banners) into clean continuous prose."""
        if not text:
            return ""
        import re

        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            l = line.strip()
            if not l:
                continue

            # 1. Éliminer les en-têtes préambules parasites de type document
            if l.upper().startswith("*DOSSIER") or l.upper().startswith("DOSSIER D'ARGUMENTATION"):
                continue
            if "Soumis à la Commission" in l or ("Commission Régionale Unifiée" in l and ("CRUI" in l or "Soumis" in l)):
                continue
            if "Cadre de référence" in l or "Loi-cadre n° 03-22" in l:
                continue
            if re.match(r"^[-=_*]{3,}$", l):
                continue

            # 2. Éliminer ou convertir les tables markdown (| col1 | col2 |)
            if l.startswith("|") and l.endswith("|"):
                if re.match(r"^\|[\s\-:|]+\|$", l):
                    continue
                parts = [p.strip() for p in l.split("|") if p.strip()]
                if len(parts) >= 2:
                    if any(h in parts[0].lower() for h in ["critère", "indicateur", "colonne", "réponse"]):
                        continue
                    l = f"{parts[0]} : {parts[1]}"
                elif len(parts) == 1:
                    l = parts[0]

            # 3. Supprimer les balises de titres (# Titre, ### 1. Titre, 1.1 Titre)
            l = re.sub(r"^#{1,6}\s*", "", l)
            l = re.sub(r"^\d+\.\d+\.?\s*", "", l)

            # 4. Supprimer le gras et italique markdown (**mot**, *mot*)
            l = re.sub(r"\*\*([^*]+)\*\*", r"\1", l)
            l = re.sub(r"\*([^*]+)\*", r"\1", l)
            l = l.replace("**", "").replace("*", "")

            # 5. Supprimer les tirets ou puces en début de ligne
            l = re.sub(r"^[-+•]\s*", "", l)

            if l:
                cleaned_lines.append(l)

        # Joindre en paragraphes cohérents
        result = " ".join(cleaned_lines)
        result = re.sub(r"[ \t]+", " ", result).strip()
        return result
