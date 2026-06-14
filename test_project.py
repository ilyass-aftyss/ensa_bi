"""
Script de validation rapide du projet BI ENSA Kénitra.
Usage : python test_project.py
"""
import sys
import os
import importlib

PYTHON_LIBS = os.path.join(os.path.dirname(__file__), "..", ".pythonlibs", "lib", "python3.11", "site-packages")
if os.path.exists(PYTHON_LIBS):
    sys.path.insert(0, PYTHON_LIBS)

ERRORS = []
PASSES = []


def check(label, fn):
    try:
        fn()
        PASSES.append(label)
        print(f"  ✅ {label}")
    except Exception as e:
        ERRORS.append((label, str(e)))
        print(f"  ❌ {label}: {e}")


# --- FastAPI ---
def test_fastapi_imports():
    from app.main import app
    from app.security import authenticate_user, create_access_token
    from app.models import Student, Grade, Filiere


def test_auth():
    from app.security import authenticate_user, create_access_token
    user = authenticate_user("admin", "admin123")
    assert user and user["role"] == "admin"
    user2 = authenticate_user("direction", "direction123")
    assert user2 and user2["role"] == "direction"
    user3 = authenticate_user("bad", "bad")
    assert user3 is None
    token = create_access_token({"sub": "admin", "role": "admin"})
    assert len(token) > 20


def test_etl_extract():
    from etl.extract import extract_all
    data = extract_all()
    assert len(data["students"]) >= 1000
    assert len(data["grades"]) >= 50000
    assert len(data["filieres"]) == 5


def test_etl_transform():
    from etl.extract import extract_all
    from etl.transform import transform_all
    raw = extract_all()
    cleaned = transform_all(raw)
    # Email manquants comblés
    assert cleaned["students"]["email"].isna().sum() == 0
    # Notes hors [0,20] supprimées
    valid = cleaned["grades"]["note"].dropna()
    assert (valid >= 0).all() and (valid <= 20).all()
    # Anomalies finance détectées
    assert "anomalie_budget" in cleaned["finance"].columns


def test_warehouse_sql():
    import os
    path = os.path.join(os.path.dirname(__file__), "warehouse", "star_schema.sql")
    assert os.path.exists(path)
    with open(path) as f:
        sql = f.read()
    assert "fact_grades" in sql
    assert "dim_student" in sql
    assert "olap_performance_par_filiere" in sql


def test_dashboard_utils():
    try:
        import streamlit  # optional on API/ETL servers
    except ImportError:
        pass  # Streamlit is only needed on Streamlit Cloud
    from dashboard.utils import ANNEES, FILIERE_COLORS, ENSA_BLUE
    assert len(ANNEES) == 5
    assert "GI-BD" in FILIERE_COLORS
    assert ENSA_BLUE.startswith("#")


print("\n" + "=" * 55)
print("  VALIDATION — ENSA KÉNITRA BI PROJECT")
print("=" * 55)
print("\n🔵 FastAPI & Sécurité")
check("Imports FastAPI/Models/Security", test_fastapi_imports)
check("Authentification JWT + RBAC", test_auth)
print("\n🔵 Pipeline ETL")
check("Extract — lecture CSV", test_etl_extract)
check("Transform — nettoyage qualité", test_etl_transform)
print("\n🔵 Data Warehouse")
check("Star Schema SQL complet", test_warehouse_sql)
print("\n🔵 Dashboard")
check("Utils & configuration Streamlit", test_dashboard_utils)
print("\n" + "=" * 55)
print(f"  Résultat : {len(PASSES)}/{len(PASSES)+len(ERRORS)} tests réussis")
if ERRORS:
    print("  Échecs :")
    for label, msg in ERRORS:
        print(f"    ✗ {label}: {msg}")
else:
    print("  🎉 Tous les tests passent !")
print("=" * 55)
sys.exit(1 if ERRORS else 0)
