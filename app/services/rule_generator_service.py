import re
import logging
from typing import Dict, Any, List, Optional
from app.schemas.rules import MagicRuleResponse, ProfileRuleSchema

logger = logging.getLogger(__name__)

# --- Référentiels Officiels Marocains ---

REFERENTIEL_REGIONS = [
    "Rabat-Salé-Kénitra",
    "Casablanca-Settat",
    "Marrakech-Safi",
    "Fès-Meknès",
    "Tanger-Tétouan-Al Hoceïma",
    "Oriental",
    "Souss-Massa",
    "Drâa-Tafilalet",
    "Béni Mellal-Khénifra",
    "Laâyoune-Sakia El Hamra",
    "Dakhla-Oued Ed-Dahab",
    "Guelmim-Oued Noun",
]

REGION_ALIASES = {
    "casablanca": "Casablanca-Settat",
    "casa": "Casablanca-Settat",
    "settat": "Casablanca-Settat",
    "rabat": "Rabat-Salé-Kénitra",
    "salé": "Rabat-Salé-Kénitra",
    "kénitra": "Rabat-Salé-Kénitra",
    "kenitra": "Rabat-Salé-Kénitra",
    "tanger": "Tanger-Tétouan-Al Hoceïma",
    "tétouan": "Tanger-Tétouan-Al Hoceïma",
    "tetouan": "Tanger-Tétouan-Al Hoceïma",
    "al hoceïma": "Tanger-Tétouan-Al Hoceïma",
    "marrakech": "Marrakech-Safi",
    "safi": "Marrakech-Safi",
    "fès": "Fès-Meknès",
    "fes": "Fès-Meknès",
    "meknès": "Fès-Meknès",
    "meknes": "Fès-Meknès",
    "agadir": "Souss-Massa",
    "souss": "Souss-Massa",
    "oujda": "Oriental",
    "nador": "Oriental",
    "berkane": "Oriental",
    "béni mellal": "Béni Mellal-Khénifra",
    "beni mellal": "Béni Mellal-Khénifra",
    "khénifra": "Béni Mellal-Khénifra",
    "khenifra": "Béni Mellal-Khénifra",
    "ouarzazate": "Drâa-Tafilalet",
    "draa": "Drâa-Tafilalet",
    "guelmim": "Guelmim-Oued Noun",
    "laâyoune": "Laâyoune-Sakia El Hamra",
    "laayoune": "Laâyoune-Sakia El Hamra",
    "dakhla": "Dakhla-Oued Ed-Dahab",
}

SECTEUR_ALIASES = {
    "automobile": "IndustrieAutomobile",
    "auto": "IndustrieAutomobile",
    "aéronautique": "AutresTransports",
    "aeronautique": "AutresTransports",
    "aéro": "AutresTransports",
    "textile": "IndustrieTextile",
    "habillement": "IndustrieHabillement",
    "chimie": "IndustrieChimique",
    "chimique": "IndustrieChimique",
    "pharmaceutique": "IndustriePharmaceutique",
    "pharma": "IndustriePharmaceutique",
    "agroalimentaire": "IndustrieAlimentaire",
    "agro": "IndustrieAlimentaire",
    "alimentation": "IndustrieAlimentaire",
    "tech": "SolutionsDigitalesNTIC",
    "technologique": "SolutionsDigitalesNTIC",
    "technologie": "SolutionsDigitalesNTIC",
    "digital": "SolutionsDigitalesNTIC",
    "logiciel": "Informatique",
    "informatique": "Informatique",
    "it": "Informatique",
    "logistique": "TransportLogistique",
    "transport": "TransportLogistique",
    "tourisme": "ActiviteTouristique",
    "touristique": "ActiviteTouristique",
    "hôtellerie": "HebergementTouristique",
    "hotellerie": "HebergementTouristique",
    "énergie": "EnergiesRenouvelables",
    "energie": "EnergiesRenouvelables",
    "renouvelable": "EnergiesRenouvelables",
    "solaire": "EnergiesRenouvelables",
    "agriculture": "EconomieRurale",
    "agricole": "EconomieRurale",
    "artisanat": "Artisanat",
}

STATUT_ALIASES = {
    "sarl": "sarl",
    "sarl-au": "sarlau",
    "sarlau": "sarlau",
    "sas": "societe-sas",
    "sa": "societe-anonyme",
    "société anonyme": "societe-anonyme",
    "auto-entrepreneur": "auto-entrepreneur",
    "autoentrepreneur": "auto-entrepreneur",
    "patente": "personne-physique-patente",
    "coopérative": "coopérative",
    "cooperative": "coopérative",
}


class RuleGeneratorService:
    """Service to translate admin natural language prompts into strict DNF eligibility profiles."""

    @classmethod
    def generate_rules(
        cls,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        llm: Optional[Any] = None
    ) -> MagicRuleResponse:
        """
        Parses an admin prompt into structured DNF profiles using LLM structured output,
        with a deterministic keyword fallback.
        """
        if not prompt or not prompt.strip():
            return MagicRuleResponse(
                success=False,
                summary="Le texte d'instruction est vide.",
                profiles=[]
            )

        program_name = context.get("name", "") if context else ""
        program_desc = context.get("description", "") if context else ""

        # 1. Tentative avec LLM si disponible
        if llm:
            try:
                structured_llm = llm.with_structured_output(MagicRuleResponse)
                system_prompt = f"""
Tu es un compilateur de règles d'éligibilité pour Tamkeen (plateforme marocaine d'accès aux subventions et aides publiques).
Ton rôle est de traduire la description en langage naturel fournie par l'administrateur en un ou plusieurs "Profils d'Éligibilité" respectant une forme normale disjonctive (DNF).

RÈGLES DNF FONDAMENTALES :
1. Chaque profil du tableau `profiles` représente une combinaison de conditions "ET".
2. S'il y a un "OU" logique dans la phrase (ex: "les entreprises à Casa OU les startups à Rabat"), tu DOIS créer plusieurs profils distincts dans le tableau `profiles`.
3. Le client sera éligible s'il valide Profil 1 OU Profil 2 OU Profil 3.
4. À l'intérieur d'un profil, toutes les conditions actives doivent être satisfaites simultanément (ET implicite).

RÉFÉRENTIELS STRICTS MAROCAINS (NE JAMAIS INVENTER D'AUTRES VALEURS) :
- Régions exactes : {REFERENTIEL_REGIONS}
- Codes secteurs recommandés :
  ['IndustrieAutomobile', 'AutresTransports', 'IndustrieTextile', 'IndustrieHabillement', 'IndustrieChimique', 'IndustriePharmaceutique', 'IndustrieAlimentaire', 'SolutionsDigitalesNTIC', 'Informatique', 'TransportLogistique', 'ActiviteTouristique', 'HebergementTouristique', 'EnergiesRenouvelables', 'EconomieRurale', 'Artisanat']
- Formes juridiques exactes : ['sarl', 'sarlau', 'societe-sas', 'societe-anonyme', 'auto-entrepreneur', 'personne-physique-patente', 'coopérative']
- Mode maturité creationMode : 'ALL' (toutes), 'NEW_UNDER_3' (moins de 3 ans / nouvelles), 'ESTABLISHED_OVER_3' (plus de 3 ans), ou 'CUSTOM'

RÈGLES DE MAPPING ET ANTI-HALLUCINATION :
- Si l'utilisateur demande une région ou un secteur qui n'est pas dans la liste exacte fournie, tu dois l'ignorer ou le mapper sur 'ALL'. Ne génère jamais de valeurs hors-référentiel.
- Si l'admin mentionne "Casablanca" ou "Tanger", mappe exactement vers "Casablanca-Settat" et "Tanger-Tétouan-Al Hoceïma" avec regionsMode="SPECIFIC".
- Si l'admin ne précise pas de région, mets regionsMode="ALL" et regions=[].
- Parsing Financier : Convertis toutes les expressions financières (1M, 500k, 2 millions) en entiers mathématiques bruts (1000000, 500000, 2000000) pour les champs caMin et caMax. Par exemple "CA supérieur à 1 million" ou "> 1M MAD" -> caMin=1000000. Si "CA < 500k", caMax=500000, hasNoCaMax=false.
- Donne à chaque profil un `name` clair et lisible (ex: "Profil 1 - Industrie Casablanca", "Profil 2 - Startups Rabat").
- Rédige un `summary` concis et professionnel en français résumant les règles configurées.

Contexte du programme : Nom: {program_name} | Description: {program_desc}
"""
                result = structured_llm.invoke(f"{system_prompt}\n\nConsigne de l'admin :\n{prompt.strip()}")
                if isinstance(result, MagicRuleResponse):
                    response_obj = result
                elif isinstance(result, dict):
                    response_obj = MagicRuleResponse(**result)
                elif hasattr(result, "model_dump"):
                    response_obj = MagicRuleResponse(**result.model_dump())
                else:
                    response_obj = MagicRuleResponse(**dict(result))

                if response_obj.profiles and len(response_obj.profiles) > 0:
                    logger.info(f"Magic Rules générées via LLM avec succès ({len(response_obj.profiles)} profils).")
                    return response_obj
            except Exception as e:
                logger.warning(f"Erreur lors de la génération de règles par LLM: {e}. Bascule sur le parseur déterministe.")

        # 2. Fallback Déterministe Heuristique
        return cls._parse_heuristics(prompt)

    @classmethod
    def _parse_heuristics(cls, prompt: str) -> MagicRuleResponse:
        """Deterministic keyword parser splitting on disjunctions ('ou', 'or') and building valid profiles."""
        lower = prompt.lower()

        # Découpage par "OU" disjonctif inter-profils :
        # - "OU" majuscule explicite (ex: " ... OU ...")
        # - "ou" précédé d'une virgule ou point-virgule (ex: "..., ou les startups...")
        # - "ou" suivi d'un déterminant/sujet ("ou aux", "ou pour", "ou les", "ou startups", etc.)
        # - saut de ligne avec puce
        # On évite ainsi de couper sur "Casablanca ou Tanger" ou "SARL ou SA" (listes intra-critère)
        branch_pattern = r'\s+(?:,\s*(?:ou|soit)\b|\bOU\b|\bou\s+(?:aux?|pour|les?|des|startups?|entreprises?|sociétés?|projets?|personnes?)\b|\n\s*[-*•]\s*|;\s*)\s*'
        branches = re.split(branch_pattern, prompt)
        branches = [b.strip() for b in branches if b.strip()]

        if not branches:
            branches = [prompt]

        profiles: List[ProfileRuleSchema] = []

        for idx, branch in enumerate(branches):
            b_lower = branch.lower()
            profile = ProfileRuleSchema(
                id=f"profile_{idx + 1}",
                name=f"Profil {idx + 1}"
            )

            # 1. Régions
            matched_regions = set()
            for alias, official_region in REGION_ALIASES.items():
                if re.search(rf'\b{re.escape(alias)}(?:s)?\b', b_lower):
                    matched_regions.add(official_region)

            for reg in REFERENTIEL_REGIONS:
                if reg.lower() in b_lower:
                    matched_regions.add(reg)

            if matched_regions:
                profile.regionsMode = "SPECIFIC"
                profile.regions = sorted(list(matched_regions))
            else:
                profile.regionsMode = "ALL"
                profile.regions = []

            # 2. Secteurs
            matched_secteurs = set()
            for alias, sect_code in SECTEUR_ALIASES.items():
                if re.search(rf'\b{re.escape(alias)}(?:s|es|x)?\b', b_lower):
                    matched_secteurs.add(sect_code)

            if matched_secteurs:
                profile.secteursMode = "SPECIFIC"
                profile.secteurs = sorted(list(matched_secteurs))
            else:
                profile.secteursMode = "ALL"
                profile.secteurs = []

            # 3. Applicant & Statut juridique
            matched_statuts = set()
            for alias, statut_code in STATUT_ALIASES.items():
                if re.search(rf'\b{re.escape(alias)}(?:s)?\b', b_lower):
                    matched_statuts.add(statut_code)

            if "personne morale" in b_lower or "société" in b_lower or "societe" in b_lower or "entreprise" in b_lower:
                profile.applicantType = "morale"
            elif "personne physique" in b_lower or "auto-entrepreneur" in b_lower or "autoentrepreneur" in b_lower:
                profile.applicantType = "physique"

            if matched_statuts:
                profile.statutsMode = "SPECIFIC"
                profile.statuts = sorted(list(matched_statuts))

            # 4. Maturité (Ancienneté)
            if re.search(r'(?:moins\s+de\s+3\s+ans|< ?3\s+ans|nouvelle|création|récente)', b_lower):
                profile.creationMode = "NEW_UNDER_3"
            elif re.search(r'(?:plus\s+de\s+3\s+ans|> ?3\s+ans|existante|établie|ancienne)', b_lower):
                profile.creationMode = "ESTABLISHED_OVER_3"

            # 5. CA (Chiffre d'affaires)
            # CA Min (ex: > 1M, supérieur à 500k, au moins 1 000 000)
            ca_min_match = re.search(
                r'(?:ca|chiffre d[\'’]affaires?)[^\d]*(?:>|≥|supérieur à|supérieure à|minimum|au moins|plus de)\s*([0-9\s.,]+)\s*(k|m|million|milliards?)?(?:\s*(?:mad|dh|dirhams?))?',
                b_lower
            )
            if ca_min_match:
                val_raw = ca_min_match.group(1).replace(' ', '').replace(',', '.')
                unit = (ca_min_match.group(2) or "").lower()
                try:
                    num = float(val_raw)
                    if num < 100_000:
                        if "m" in unit:
                            num *= 1_000_000
                        elif "k" in unit:
                            num *= 1_000
                    profile.caMin = int(num)
                except ValueError:
                    pass

            # CA Max (ex: < 10M, inférieur à 5 millions)
            ca_max_match = re.search(
                r'(?:ca|chiffre d[\'’]affaires?)[^\d]*(?:<|≤|inférieur à|inférieure à|maximum|au plus|plafond de)\s*([0-9\s.,]+)\s*(k|m|million|milliards?)?(?:\s*(?:mad|dh|dirhams?))?',
                b_lower
            )
            if ca_max_match:
                val_raw = ca_max_match.group(1).replace(' ', '').replace(',', '.')
                unit = (ca_max_match.group(2) or "").lower()
                try:
                    num = float(val_raw)
                    if num < 100_000:
                        if "m" in unit:
                            num *= 1_000_000
                        elif "k" in unit:
                            num *= 1_000
                    profile.caMax = int(num)
                    profile.hasNoCaMax = False
                except ValueError:
                    pass

            # Nommage intelligent du profil
            name_parts = []
            if profile.secteurs:
                name_parts.append(profile.secteurs[0])
            if profile.regions:
                name_parts.append(profile.regions[0].split('-')[0])
            if profile.caMin:
                name_parts.append(f"CA≥{int(profile.caMin):,}".replace(",", " "))

            if name_parts:
                profile.name = f"Profil {idx + 1} - {' / '.join(name_parts)}"

            profiles.append(profile)

        summary_text = (
            f"{len(profiles)} profil(s) d'éligibilité identifié(s) : " +
            " OU ".join([p.name for p in profiles]) + "."
        )

        return MagicRuleResponse(
            success=True,
            summary=summary_text,
            profiles=profiles
        )
