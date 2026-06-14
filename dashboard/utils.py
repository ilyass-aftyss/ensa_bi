"""
Utilitaires Dashboard — connexion API, cache, styling.
Version 2.0 — authentification manuelle via session_state JWT.
"""
from __future__ import annotations
import os
import requests

try:
    import streamlit as st
except ImportError:
    st = None

API_URL = os.getenv("API_URL", "http://localhost:8000")

ANNEES = ["2024-2025", "2023-2024", "2022-2023", "2021-2022", "2020-2021"]

FILIERE_COLORS = {
    "GI-BD":   "#2563EB",
    "GI-GL":   "#16A34A",
    "GSTR":    "#D97706",
    "GINDUS":  "#9333EA",
    "GEN":     "#64748B",
}

ENSA_BLUE = "#1E3A5F"
ENSA_GOLD = "#C9A227"


def _get_token() -> str:
    """Renvoie le JWT stocke dans session_state (login manuel)."""
    return st.session_state.get("token", "") if st else ""


def api_get(path: str, params: dict = None) -> dict | list | None:
    """Appel GET authentifie vers l'API."""
    token = _get_token()
    if not token:
        if st:
            st.error("Session expiree. Veuillez vous reconnecter.")
        return None
    try:
        r = requests.get(
            f"{API_URL}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        if st:
            st.error("API non disponible. Verifiez que le serveur FastAPI est demarre.")
        return None
    except requests.exceptions.HTTPError as e:
        if st and e.response.status_code != 403:
            st.error(f"Erreur API {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        if st:
            st.error(f"Erreur inattendue : {e}")
        return None


def kpi_card(label: str, value: str, delta: str = "", color: str = ENSA_BLUE, icon: str = ""):
    delta_html = f"<span style='font-size:0.8rem;color:#6b7280'>{delta}</span>" if delta else ""
    st.markdown(
        f"""
        <div style='
            background:white;border-radius:12px;padding:1.2rem 1.5rem;
            box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid {color};
            margin-bottom:0.5rem;
        '>
            <div style='font-size:0.78rem;color:#6b7280;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.05em;margin-bottom:0.3rem'>{icon} {label}</div>
            <div style='font-size:2rem;font-weight:800;color:{color};line-height:1.1'>{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(label: str, status: str = "ok"):
    colors = {"ok": "#16a34a", "warn": "#d97706", "error": "#dc2626"}
    icons  = {"ok": "✓", "warn": "⚠", "error": "✗"}
    c = colors.get(status, "#6b7280")
    i = icons.get(status, "•")
    st.markdown(
        f"<span style='background:{c}20;color:{c};padding:2px 10px;border-radius:20px;"
        f"font-size:0.75rem;font-weight:600'>{i} {label}</span>",
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"<h3 style='color:{ENSA_BLUE};margin-top:1.5rem;margin-bottom:0.2rem'>{title}</h3>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"<p style='color:#6b7280;font-size:0.9rem;margin-bottom:1rem'>{subtitle}</p>",
            unsafe_allow_html=True,
        )


def apply_global_style():
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{ background:#f8fafc; }}
        [data-testid="stSidebar"]          {{ background:{ENSA_BLUE}; }}
        [data-testid="stSidebar"] * {{ color:white !important; }}
        [data-testid="stSidebar"] .stSelectbox label {{ color:white !important; }}
        h1,h2,h3 {{ color:{ENSA_BLUE}; }}
        .block-container {{ padding-top:1.5rem; }}
        div[data-testid="metric-container"] {{
            background:white;border-radius:12px;
            padding:1rem;box-shadow:0 2px 8px rgba(0,0,0,0.07);
        }}

        /* Bouton Se deconnecter — texte noir */
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button p,
        [data-testid="stSidebar"] .stButton > button span {{
            color: #111827 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )