# 🤖 Tamkeen MLOps — Le Consultant Virtuel

Microservice IA propulsant le « Consultant Virtuel » pour la plateforme **Tamkeen** :
- **Extraction Documentaire Intelligente :** Parsing des pièces juridiques et fiscales marocaines (Attestation Fiscale, Registre de Commerce, Attestation d'Affiliation CNSS) via `pdfplumber` et LLM / regex heuristiques.
- **Rédaction Experte par IA :** Génération automatisée des argumentaires économiques, territoriaux, d'impact socio-économique et de viabilité financière alignés avec la Charte de l'Investissement marocaine (Loi-cadre n° 03-22).
- **Orchestration LangGraph :** Machine d'état asynchrone sécurisée, résiliente et communiquant via Webhooks avec le backend Express/MySQL.

---

## 🏗️ Architecture Modulaire

Le projet suit une architecture modulaire en couches garantissant séparation des responsabilités, testabilité et extensibilité :

```text
masubvention_mlops/
├── app/
│   ├── api/                   # Couche Présentation (FastAPI Routers & Endpoints)
│   │   └── v1/
│   │       ├── endpoints/     # /extract, /health
│   │       └── router.py      # Agrégateur des routes v1
│   ├── core/                  # Configuration, Settings & LLM Factory
│   │   ├── config.py
│   │   └── llm_factory.py
│   ├── schemas/               # Modèles de données typés (Pydantic v2)
│   │   ├── extraction.py      # Requêtes d'extraction & payloads
│   │   ├── legal.py           # Informations légales entreprise
│   │   └── narrative.py       # Rapport d'argumentaires
│   ├── services/              # Services Métier & Domaine
│   │   ├── pdf_service.py     # Parsing PDF & extraction heuristique
│   │   ├── consultant_service.py # Prompting LLM & fallback déterministe
│   │   └── webhook_service.py # Émission webhook vers Express
│   └── workflow/              # Orchestration LangGraph
│       ├── state.py           # WorkflowState TypedDict
│       ├── nodes.py           # Nœuds du graphe
│       └── graph.py           # Compilation & exécution du graphe
├── main.py                    # Point d'entrée de l'application FastAPI
├── test_pipeline.py           # Suite de tests automatisés (100% sans mocks externes requis)
├── requirements.txt           # Dépendances Python
└── .env.example               # Modèle de variables d'environnement
```

---

## ⚙️ Installation & Démarrage

### 1. Prérequis
- Python 3.10+
- Environnement virtuel recommandé (`venv`)

### 2. Configuration
```bash
cp .env.example .env
# Éditez .env pour renseigner vos clés LLM (DeepSeek ou OpenAI) si disponibles
```

### 3. Installation des dépendances
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Démarrage du serveur
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Le serveur sera accessible sur `http://localhost:8000`.
Documentation interactive Swagger disponible sur `http://localhost:8000/docs`.

---

## 🧪 Tests Unitaires & Intégration

Exécuter la suite de tests avec l'environnement virtuel :
```bash
./venv/bin/python test_pipeline.py
# ou
pytest
```

---

## 📡 Points d'Accès API Principaux

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Healthcheck du microservice et statut opérationnel |
| `POST` | `/api/v1/extract` | Déclenche l'extraction asynchrone des 3 PDF et la rédaction du mémorandum |

---

## 🔒 Résilience & Mode Sans LLM
Le service est conçu pour une résilience maximale :
- Si aucune clé API LLM (`DEEPSEEK_API_KEY` ou `OPENAI_API_KEY`) n'est fournie ou en cas d'indisponibilité réseau, le service bascule automatiquement sur un parseur heuristique regex robuste et un générateur déterministe d'argumentaires experts calibré selon les ratios de la Charte de l'Investissement.
