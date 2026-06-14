# 🎓 ENSA Kénitra — Architecture BI Sécurisée

> Système Business Intelligence complet pour l'ENSA de Kénitra.  
> **Équipe** : AFTYSS Ilyass · ABDELMOUMEN Med Amine · BENHADDANE Anas  
> **Année universitaire** : 2024-2025 | Encadrant : Pr. Aniss MOUMEN

---

## 🏗 Architecture Globale

```
                         ┌─────────────────────────┐
                         │   Sources de Données     │
                         │  (CSV / Excel / Registres)│
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │    ETL Pipeline          │
                         │  extract → transform     │
                         │       → load             │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────▼──────────────────────┐
              │         PostgreSQL (Railway)                   │
              │  OLTP Tables  →  Data Warehouse (Étoile)       │
              │  Vues OLAP  ·  Audit Logs  ·  RBAC            │
              └───────────────┬──────────────────────────────┘
                              │
              ┌───────────────▼──────────────────────────────┐
              │         FastAPI (Railway)                      │
              │  /auth/token  /students  /kpi/*               │
              │  JWT Auth · RBAC (admin/direction/professeur) │
              └───────────────┬──────────────────────────────┘
                              │ HTTP REST
              ┌───────────────▼──────────────────────────────┐
              │      Dashboard Streamlit (Streamlit Cloud)     │
              │  Vue Générale · Performance · Finance · RH    │
              └──────────────────────────────────────────────┘
```

---

## 📁 Structure du Projet

```
bi-project/
├── app/                          # API FastAPI
│   ├── main.py                   # Point d'entrée
│   ├── database.py               # Connexion SQLAlchemy
│   ├── models.py                 # Modèles ORM (tables OLTP)
│   ├── security.py               # JWT + RBAC
│   └── routers/
│       ├── auth.py               # POST /auth/token
│       ├── students.py           # GET /students/*
│       └── kpi.py                # GET /kpi/*
│
├── etl/                          # Pipeline ETL
│   ├── generate_data.py          # Génération données synthétiques ENSA
│   ├── extract.py                # Lecture CSV → DataFrames
│   ├── transform.py              # Nettoyage + validation qualité
│   ├── load.py                   # Chargement PostgreSQL
│   └── run_etl.py                # Orchestrateur (--generate, --no-load)
│
├── warehouse/                    # Data Warehouse
│   ├── star_schema.sql           # Schéma en étoile + vues OLAP
│   └── create_warehouse.py       # Peuplement DIM + FACT tables
│
├── dashboard/                    # Dashboard Streamlit
│   ├── streamlit_app.py          # Page principale (Vue Générale)
│   ├── utils.py                  # Helpers (API, style, KPI cards)
│   └── pages/
│       ├── 1_Performance_Academique.py
│       ├── 2_Ressources.py
│       ├── 3_Finance.py
│       └── 4_RH.py
│
├── data/raw/                     # Données brutes générées (gitignored)
├── .streamlit/config.toml        # Configuration Streamlit
├── requirements.txt              # Dépendances API + ETL
├── requirements-dashboard.txt    # Dépendances Dashboard uniquement
├── Procfile                      # Commande de démarrage Railway
├── railway.toml                  # Configuration Railway
├── .env.example                  # Template variables d'environnement
└── README.md
```

---

## ⚙️ Installation locale

### Prérequis

- Python 3.11+
- PostgreSQL (local ou Railway)
- Git

### 1. Cloner et configurer

```bash
git clone https://github.com/votre-username/ensa-bi.git
cd ensa-bi/bi-project

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

**Variables obligatoires :**

| Variable | Description | Exemple |
|---|---|---|
| `DATABASE_URL` | URL PostgreSQL | `postgresql://user:pass@host:5432/ensa_bi` |
| `SECRET_KEY` | Clé JWT (aléatoire) | `openssl rand -hex 32` |
| `API_URL` | URL de l'API (pour Streamlit) | `https://your-app.up.railway.app` |

### 3. Initialiser la base de données

```bash
# Créer la base de données PostgreSQL
psql -U postgres -c "CREATE DATABASE ensa_bi;"

# Générer les données + ETL complet
python -m etl.run_etl --generate

# Construire le Data Warehouse (schéma en étoile)
python -m warehouse.create_warehouse
```

### 4. Démarrer l'API

```bash
uvicorn app.main:app --reload --port 8000
# Documentation interactive : http://localhost:8000/docs
```

### 5. Démarrer le Dashboard

```bash
streamlit run dashboard/streamlit_app.py
# Accès : http://localhost:8501
```

---

## ☁️ Déploiement Railway (API + PostgreSQL)

### Étape 1 — Créer un projet Railway

1. Aller sur [railway.app](https://railway.app) → **New Project**
2. **Add PostgreSQL** → Railway crée automatiquement `DATABASE_URL`

### Étape 2 — Déployer l'API FastAPI

```bash
# Depuis le répertoire bi-project/
railway login
railway link       # lier au projet Railway
railway up         # déployer
```

Ou via GitHub :
1. Pusher le code sur GitHub
2. Dans Railway : **New Service → GitHub Repo**
3. Sélectionner le repo → Railway détecte automatiquement le `Procfile`

### Étape 3 — Configurer les variables d'environnement Railway

Dans le tableau de bord Railway → **Variables** :

```
DATABASE_URL     = (automatiquement injecté par Railway PostgreSQL)
SECRET_KEY       = votre-clé-secrète-générée
API_URL          = https://votre-service.up.railway.app
```

### Étape 4 — Exécuter l'ETL sur Railway

```bash
# Depuis le terminal Railway ou en tant que one-off job
railway run python -m etl.run_etl --generate

# Construire le Data Warehouse
railway run python -m warehouse.create_warehouse
```

### Étape 5 — Vérification

```bash
# Tester l'API déployée
curl https://votre-service.up.railway.app/healthz
# → {"status": "ok"}
```

---

## 🌐 Déploiement Streamlit Cloud

### Prérequis

- Compte GitHub avec le code poussé
- Compte [share.streamlit.io](https://share.streamlit.io)

### Étape 1 — Préparer le repo GitHub

```bash
git add .
git commit -m "feat: architecture BI ENSA Kénitra"
git push origin main
```

### Étape 2 — Déployer sur Streamlit Cloud

1. Aller sur [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Sélectionner votre repo GitHub
3. **Main file path** : `bi-project/dashboard/streamlit_app.py`
4. **Requirements file** : `bi-project/requirements-dashboard.txt`

### Étape 3 — Configurer les secrets Streamlit

Dans **Settings → Secrets** :

```toml
API_URL = "https://votre-api.up.railway.app"
API_USER = "admin"
API_PASS = "admin123"
```

### Étape 4 — Déployer

Cliquer **Deploy** — Streamlit Cloud installe les dépendances et lance l'app.

---

## 🔐 Authentification & RBAC

### Rôles disponibles

| Rôle | Accès | Credentials par défaut |
|---|---|---|
| `admin` | Tout (lecture, écriture, finances, RH) | `admin / admin123` |
| `direction` | Lecture + KPI + Finances | `direction / direction123` |
| `professeur` | Lecture + KPI notes | `professeur / prof123` |

### Obtenir un token JWT

```bash
curl -X POST "https://votre-api.up.railway.app/auth/token" \
  -d "username=admin&password=admin123"

# Réponse:
# {"access_token": "eyJ...", "token_type": "bearer", "role": "admin"}
```

### Utiliser le token

```bash
curl -H "Authorization: Bearer eyJ..." \
  "https://votre-api.up.railway.app/kpi/dashboard-overview?annee_universitaire=2024-2025"
```

---

## 📊 Endpoints API

| Méthode | Endpoint | Description | Rôle |
|---|---|---|---|
| `POST` | `/auth/token` | Obtenir un token JWT | Public |
| `GET` | `/students/` | Liste étudiants (paginée) | Tous |
| `GET` | `/students/count` | Nombre total d'étudiants | Tous |
| `GET` | `/students/by-filiere` | Répartition par filière | Tous |
| `GET` | `/students/evolution` | Évolution inscriptions | Tous |
| `GET` | `/kpi/success-rate` | Taux de réussite | Tous |
| `GET` | `/kpi/abandon-rate` | Taux d'abandon | Tous |
| `GET` | `/kpi/avg-grade` | Moyenne générale | Tous |
| `GET` | `/kpi/budget-usage` | Exécution budgétaire | direction, admin |
| `GET` | `/kpi/top-filieres` | Classement filières | Tous |
| `GET` | `/kpi/teacher-workload` | Charge enseignants | Tous |
| `GET` | `/kpi/room-occupancy` | Occupation salles | Tous |
| `GET` | `/kpi/enrollments-summary` | Résumé inscriptions | Tous |
| `GET` | `/kpi/dashboard-overview` | Vue globale dashboard | Tous |
| `GET` | `/healthz` | Health check | Public |
| `GET` | `/docs` | Documentation Swagger | Public |

---

## 🔄 Pipeline ETL

```bash
# Générer + ETL complet
python -m etl.run_etl --generate

# ETL seul (si données déjà générées)
python -m etl.run_etl

# Dry-run (extract + transform uniquement, sans écriture DB)
python -m etl.run_etl --no-load

# Rebuild Data Warehouse
python -m warehouse.create_warehouse
```

---

## 🏗 Data Warehouse — Schéma en Étoile

```
                    ┌──────────────┐
                    │   dim_time   │
                    │  time_id  PK │
                    └──────┬───────┘
                           │
    ┌──────────────┐  ┌────▼──────────┐  ┌──────────────┐
    │ dim_student  │  │  fact_grades  │  │  dim_course  │
    │ student_id PK│◄─┤  grade_id  PK ├─►│  course_id PK│
    └──────┬───────┘  │  note         │  └──────┬───────┘
           │          └───────────────┘         │
    ┌──────▼───────┐                     ┌──────▼───────┐
    │ dim_filiere  │                     │  dim_teacher │
    │ filiere_id PK│                     │ teacher_id PK│
    └──────────────┘                     └──────────────┘
```

**Tables de faits :** `fact_grades`, `fact_enrollments`, `fact_finance`, `fact_teaching`, `fact_schedule`  
**Vues OLAP :** `olap_performance_par_filiere`, `olap_inscriptions`, `olap_budget_execution`, `olap_charge_enseignants`, `olap_occupation_salles`

---

## 🔒 Sécurité (Loi 09-08 & Privacy by Design)

- **RBAC** : Contrôle d'accès granulaire par rôle
- **JWT** : Tokens signés HS256, expiration configurable
- **HTTPS** : Obligatoire en production (Railway + Streamlit Cloud assurent le TLS)
- **Chiffrement** : Variables sensibles dans `.env` / Railway Variables / Streamlit Secrets
- **Audit** : Tous les accès API loggés
- **Données personnelles** : Emails et données étudiants protégés (RBAC)

---

## 🧪 Test rapide

```bash
# 1. Démarrer l'API
uvicorn app.main:app --reload &

# 2. Obtenir un token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=admin123" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Tester un KPI
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/kpi/dashboard-overview?annee_universitaire=2024-2025"
```

---

## 📦 Dépendances principales

| Package | Version | Usage |
|---|---|---|
| `fastapi` | 0.115.5 | API REST |
| `uvicorn` | 0.32.1 | Serveur ASGI |
| `sqlalchemy` | 2.0.36 | ORM |
| `psycopg2-binary` | 2.9.10 | Connecteur PostgreSQL |
| `pandas` | 2.2.3 | ETL / Transformation |
| `python-jose` | 3.3.0 | JWT |
| `passlib[bcrypt]` | 1.7.4 | Hash mots de passe |
| `streamlit` | 1.40.2 | Dashboard |
| `plotly` | 5.24.1 | Graphiques interactifs |

---

*Projet académique — ENSA Kénitra | Architecture BI Sécurisée | 2024-2025*
#   e n s a _ b i  
 