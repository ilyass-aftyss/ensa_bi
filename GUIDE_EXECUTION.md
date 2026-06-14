# Guide d'exécution complet — ENSA Kénitra BI

Ce guide couvre **3 scénarios** : exécution locale, déploiement Railway, déploiement Streamlit Cloud.

---

## Prérequis système

| Outil | Version minimum | Vérification |
|-------|----------------|-------------|
| Python | 3.10+ | `python --version` |
| pip | 23+ | `pip --version` |
| PostgreSQL | 14+ | `psql --version` |
| Git | 2.x | `git --version` |

---

## SCÉNARIO 1 — Exécution locale complète

### Étape 1 — Cloner et se placer dans le projet

```bash
git clone <url-du-repo>
cd bi-project
```

### Étape 2 — Créer un environnement virtuel Python

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Étape 3 — Installer les dépendances

> ⚠️ L'ordre des commandes est important pour bcrypt

```bash
pip install --upgrade pip

# Installer bcrypt d'abord, en version exacte 4.0.1
pip install bcrypt==4.0.1

# Installer toutes les dépendances API + ETL
pip install -r requirements.txt
```

### Étape 4 — Créer la base de données PostgreSQL locale

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Dans psql, créer la base
CREATE DATABASE ensa_bi;
\q
```

### Étape 5 — Configurer les variables d'environnement

```bash
# Copier le fichier exemple
cp .env.example .env
```

Ouvrir `.env` et remplir :

```env
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE@localhost:5432/ensa_bi
SECRET_KEY=une-cle-aleatoire-longue-et-securisee
ACCESS_TOKEN_EXPIRE_MINUTES=60
API_URL=http://localhost:8000
API_USER=admin
API_PASS=admin123
ENVIRONMENT=development
LOG_LEVEL=INFO
```

> Pour générer une SECRET_KEY sécurisée :
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### Étape 6 — Lancer le pipeline ETL (génère + charge les données)

```bash
# Depuis le dossier bi-project/
python -m etl.run_etl --generate
```

Résultat attendu :
```
ETL ENSA KÉNITRA — Démarrage ...
Étape 0 — Génération des données brutes...
Étape 1 — Extraction...
  students: 1200 lignes extraites
  grades: 59540 lignes extraites
  ...
Étape 2 — Transformation...
Étape 3 — Chargement PostgreSQL...
ETL terminé en ~5s
```

> Si vous avez déjà les CSV dans `data/raw/`, utilisez sans `--generate` :
> ```bash
> python -m etl.run_etl
> ```

### Étape 7 — Construire le Data Warehouse

```bash
python -m warehouse.create_warehouse
```

Résultat attendu :
```
Schéma en étoile appliqué.
dim_time: 10 périodes insérées.
dim_filiere: 5 lignes.
dim_student: 1200 lignes.
...
fact_grades: 59540 lignes.
✅ Data Warehouse construit avec succès.
```

### Étape 8 — Démarrer l'API FastAPI

```bash
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Vérification : ouvrir http://localhost:8000/docs  
Vous devez voir l'interface Swagger avec tous les endpoints.

### Étape 9 — Tester l'API (optionnel)

```bash
# Obtenir un token JWT
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Réponse attendue :
# {"access_token":"eyJ...","token_type":"bearer"}

# Tester un endpoint protégé
curl http://localhost:8000/kpi/overview \
  -H "Authorization: Bearer eyJ..."
```

### Étape 10 — Démarrer le Dashboard Streamlit

Ouvrir un **second terminal** (garder uvicorn actif dans le premier) :

```bash
# Installer les dépendances Streamlit
pip install -r requirements-dashboard.txt

# Lancer le dashboard
streamlit run dashboard/streamlit_app.py
```

Ouvrir http://localhost:8501 — le dashboard se connecte à l'API sur le port 8000.

---

## SCÉNARIO 2 — Déploiement Railway (API + BDD)

### Étape 1 — Préparer le dépôt GitHub

```bash
git add .
git commit -m "deploy: ENSA BI initial"
git push origin main
```

### Étape 2 — Créer le projet Railway

1. Aller sur [railway.app](https://railway.app) → **New Project**
2. Choisir **Deploy from GitHub repo** → sélectionner votre repo
3. Railway détecte automatiquement le `Procfile` :
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Étape 3 — Ajouter PostgreSQL

Dans Railway → **+ New Service** → **PostgreSQL**  
Railway injecte automatiquement `DATABASE_URL` dans votre service.

### Étape 4 — Définir les variables d'environnement Railway

Dans votre service API → onglet **Variables** → ajouter :

| Variable | Valeur |
|----------|--------|
| `SECRET_KEY` | (votre clé générée, ex: `d7cb32a51e40ce7f...`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |

> `DATABASE_URL` est déjà injectée automatiquement par Railway — ne pas la redéfinir.

### Étape 5 — Configurer le répertoire racine Railway

Dans votre service → **Settings** → **Root Directory** :  
```
bi-project
```

> ⚠️ Ce réglage est crucial. Sans lui, Railway cherche `Procfile` à la racine du repo et ne le trouve pas.

### Étape 6 — Lancer l'ETL post-déploiement

Une fois le service déployé, dans Railway → **Shell** (ou CLI Railway) :

```bash
# Générer et charger toutes les données
python -m etl.run_etl --generate

# Construire le Data Warehouse
python -m warehouse.create_warehouse
```

### Étape 7 — Vérifier le déploiement

Railway affiche votre URL publique (ex: `https://ensa-bi-api.up.railway.app`)

```bash
curl https://ensa-bi-api.up.railway.app/healthz
# Réponse : {"status":"ok"}

curl https://ensa-bi-api.up.railway.app/docs
# Interface Swagger accessible
```

---

## SCÉNARIO 3 — Déploiement Streamlit Cloud (Dashboard)

### Étape 1 — Aller sur Streamlit Cloud

[share.streamlit.io](https://share.streamlit.io) → **New app**

### Étape 2 — Configurer le déploiement

| Champ | Valeur |
|-------|--------|
| Repository | `votre-user/votre-repo` |
| Branch | `main` |
| Main file path | `bi-project/dashboard/streamlit_app.py` |

Cliquer sur **Advanced settings** → **Python packages file** :
```
bi-project/requirements-dashboard.txt
```

### Étape 3 — Configurer les Secrets Streamlit

Dans **Advanced settings** → **Secrets** (format TOML) :

```toml
API_URL = "https://ensa-bi-api.up.railway.app"
API_USER = "admin"
API_PASS = "admin123"
```

### Étape 4 — Déployer

Cliquer **Deploy** — Streamlit Cloud prend 2-5 minutes pour builder.

---

## Identifiants par défaut

| Rôle | Nom d'utilisateur | Mot de passe | Accès |
|------|-------------------|-------------|-------|
| Admin | `admin` | `admin123` | Tout |
| Direction | `direction` | `direction123` | KPI + Finances |
| Professeur | `professeur` | `prof123` | Lecture + Notes |

---

## Erreurs fréquentes et solutions

### ❌ `ModuleNotFoundError: No module named 'app'`

**Cause** : Vous n'êtes pas dans le dossier `bi-project/`

**Solution** :
```bash
cd bi-project
python -m etl.run_etl --generate
```

---

### ❌ `ERROR: bcrypt 5.x.x is not compatible with passlib`

**Cause** : Version de bcrypt incorrecte

**Solution** :
```bash
pip uninstall bcrypt -y
pip install bcrypt==4.0.1
```

---

### ❌ `sqlalchemy.exc.OperationalError: connection refused`

**Cause** : PostgreSQL n'est pas lancé ou `DATABASE_URL` est incorrecte

**Solution** :
```bash
# Vérifier que PostgreSQL tourne
pg_isready -h localhost -p 5432

# Vérifier la valeur dans .env
cat .env | grep DATABASE_URL

# Format correct :
# DATABASE_URL=postgresql://postgres:motdepasse@localhost:5432/ensa_bi
```

---

### ❌ `psycopg2.OperationalError: FATAL: database "ensa_bi" does not exist`

**Cause** : La base de données n'a pas été créée

**Solution** :
```bash
psql -U postgres -c "CREATE DATABASE ensa_bi;"
```

---

### ❌ `FileNotFoundError: data/raw/students.csv`

**Cause** : L'ETL n'a jamais été lancé avec `--generate`

**Solution** :
```bash
python -m etl.run_etl --generate
```

---

### ❌ Railway : `No start command found`

**Cause** : Root directory non configuré sur `bi-project`

**Solution** :  
Railway → Service → Settings → Root Directory → taper `bi-project` → Save

---

### ❌ Streamlit : `ConnectionError: Cannot connect to API`

**Cause** : `API_URL` pointe encore vers `localhost:8000`

**Solution** :  
Streamlit Cloud → App settings → Secrets → remplacer `API_URL` par l'URL Railway publique

---

## Validation complète (vérification rapide)

```bash
cd bi-project
python test_project.py
```

Résultat attendu :
```
Résultat : 6/6 tests réussis
🎉 Tous les tests passent !
```

---

## Ordre d'exécution obligatoire

```
1. pip install bcrypt==4.0.1
2. pip install -r requirements.txt
3. Configurer .env (DATABASE_URL + SECRET_KEY)
4. python -m etl.run_etl --generate    ← TOUJOURS avant le DW
5. python -m warehouse.create_warehouse
6. uvicorn app.main:app --reload --port 8000
7. streamlit run dashboard/streamlit_app.py  (second terminal)
```
