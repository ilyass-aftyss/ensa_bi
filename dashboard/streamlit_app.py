"""
Dashboard Principal — ENSA Kenitra BI v2.0
Page d'accueil avec authentification et vue adaptee au role.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.auth_ui import require_auth, render_login_page, render_sidebar_nav
from dashboard.utils import (
    api_get, kpi_card, section_header, status_badge,
    apply_global_style, ANNEES, FILIERE_COLORS, ENSA_BLUE, ENSA_GOLD,
)

st.set_page_config(
    page_title="BI ENSA Kenitra",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Authentification ──────────────────────────────────────────────────────────
if not st.session_state.get("authenticated"):
    render_login_page()

apply_global_style()

# ── Fix couleur texte inputs / selectbox dans la sidebar ─────────────────────
st.markdown("""
<style>
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] .stTextInput input {
    color: #1e293b !important;
    background-color: #f8fafc !important;
}

section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] div,
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: #1e293b !important;
    background-color: #f8fafc !important;
}

section[data-testid="stSidebar"] [data-baseweb="popover"] li,
section[data-testid="stSidebar"] [data-baseweb="menu"] li {
    color: #1e293b !important;
}
</style>
""", unsafe_allow_html=True)

render_sidebar_nav()

user = {
    "role":       st.session_state.get("role"),
    "full_name":  st.session_state.get("full_name"),
    "student_id": st.session_state.get("student_id"),
    "teacher_id": st.session_state.get("teacher_id"),
}
role = user["role"]

# ── Redirect etudiant vers Mon Espace ────────────────────────────────────────
if role == "etudiant":
    st.switch_page("pages/0_Mon_Espace.py")

# ── Sidebar filtres ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    annee = st.selectbox("Annee universitaire", ANNEES, index=0)

# ============================================================
# VUE ENSEIGNANT
# ============================================================
if role == "enseignant":
    teacher_id = user.get("teacher_id")

    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.markdown(
            f"<h1 style='margin-bottom:0'>Tableau de bord Enseignant</h1>"
            f"<p style='color:#6b7280;font-size:0.9rem'>"
            f"Bienvenue, {user['full_name']} &nbsp;|&nbsp; "
            f"<span style='color:#2563eb;font-weight:600'>📚 Enseignant</span></p>",
            unsafe_allow_html=True,
        )
    with col_badge:
        st.markdown("<br>", unsafe_allow_html=True)
        status_badge("Connecte", "ok")

    st.markdown("---")

    with st.spinner("Chargement de vos donnees..."):
        my_courses = api_get("/teachers/me/courses") or []
        my_perf    = api_get("/teachers/me/students-performance", {"annee_universitaire": annee}) or []

    # KPI cards
    total_heures = sum(c.get("heures", 0) for c in my_courses)
    total_students = sum(c.get("nb_etudiants", 0) for c in my_courses)
    avg_global = (
        sum(p.get("moyenne", 0) for p in my_perf) / len(my_perf) if my_perf else 0
    )
    avg_reussite = (
        sum(p.get("taux_reussite_pct", 0) for p in my_perf) / len(my_perf) if my_perf else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Cours assures", str(len(my_courses)), "Total", ENSA_BLUE, "📖")
    with c2: kpi_card("Heures / sem.", f"{total_heures}h", "Charge totale", "#2563eb", "⏱️")
    with c3: kpi_card("Etudiants", f"{total_students:,}", "Dans mes cours", "#16a34a", "👥")
    with c4: kpi_card("Taux reussite", f"{avg_reussite:.1f}%", f"Annee {annee}", "#d97706", "🏆")

    st.markdown("<br>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)

    with g1:
        section_header("Performance par cours")
        if my_perf:
            df_p = pd.DataFrame(my_perf)
            fig = px.bar(
                df_p.sort_values("moyenne", ascending=True),
                x="moyenne", y="cours", orientation="h",
                color="taux_reussite_pct",
                color_continuous_scale=["#dc2626", "#d97706", "#16a34a"],
                labels={"moyenne": "Moyenne /20", "cours": "Cours", "taux_reussite_pct": "Reussite %"},
                text="moyenne",
            )
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig.update_layout(
                height=350, margin=dict(t=10, b=10, l=10, r=10),
                plot_bgcolor="white", paper_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Donnees non disponibles pour cette annee.")

    with g2:
        section_header("Mes cours")
        if my_courses:
            df_c = pd.DataFrame(my_courses)[["nom", "filiere", "heures", "nb_etudiants", "moyenne"]]
            df_c.columns = ["Cours", "Filiere", "Heures", "Etudiants", "Moyenne"]
            df_c["Moyenne"] = df_c["Moyenne"].apply(
                lambda x: f"{x:.1f}" if x is not None else "—"
            )
            st.dataframe(df_c, hide_index=True, use_container_width=True)
        else:
            st.info("Aucun cours trouve.")

# ============================================================
# VUE DIRECTION / ADMINISTRATEUR
# ============================================================
else:
    col_title, col_status = st.columns([3, 1])
    with col_title:
        role_badge = "🛡️ Administrateur" if role == "administrateur" else "🎯 Direction"
        st.markdown(
            f"<h1 style='margin-bottom:0'>Tableau de bord — ENSA Kenitra</h1>"
            f"<p style='color:#6b7280;font-size:0.9rem'>Accueil › Vue generale &nbsp;|&nbsp; "
            f"<span style='color:#16a34a;font-weight:600'>● {annee}</span> &nbsp;|&nbsp; {role_badge}</p>",
            unsafe_allow_html=True,
        )
    with col_status:
        st.markdown("<br>", unsafe_allow_html=True)
        status_badge("ETL actif", "ok")
        status_badge("DW sync", "ok")

    st.markdown("---")

    with st.spinner("Chargement des donnees..."):
        overview     = api_get("/kpi/dashboard-overview", {"annee_universitaire": annee}) or {}
        success_data = api_get("/kpi/success-rate", {"annee_universitaire": annee}) or []
        abandon_data = api_get("/kpi/abandon-rate", {"annee_universitaire": annee}) or []
        evolution    = api_get("/students/evolution") or []
        by_filiere   = api_get("/students/by-filiere") or []
        budget_data  = api_get("/kpi/budget-usage", {"annee_universitaire": annee}) or {}
        top_filieres = api_get("/kpi/top-filieres", {"annee_universitaire": annee}) or []

    # KPI Cards
    st.markdown(
        "<p style='font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;"
        "letter-spacing:0.08em'>INDICATEURS CLES</p>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Effectif", f"{overview.get('total_etudiants', 0):,}", "Etudiants inscrits", ENSA_BLUE, "👥")
    with c2:
        taux_r = overview.get("taux_reussite_global_pct", 0)
        kpi_card("Reussite", f"{taux_r:.1f}%", "Taux de reussite global", "#16a34a", "🏆")
    with c3:
        taux_a = overview.get("taux_abandon_global_pct", 0)
        color_a = "#dc2626" if taux_a > 8 else "#d97706" if taux_a > 5 else "#16a34a"
        kpi_card("Abandon", f"{taux_a:.1f}%", "Taux d'abandon", color_a, "📉")
    with c4:
        taux_b = overview.get("taux_execution_budgetaire_pct", 0)
        kpi_card("Budget", f"{taux_b:.1f}%", "Execution budgetaire", ENSA_GOLD, "💰")

    st.markdown("<br>", unsafe_allow_html=True)

    g1, g2 = st.columns([3, 2])

    with g1:
        section_header("Evolution des inscriptions par departement")
        if evolution:
            df_evo = pd.DataFrame(evolution)
            if not df_evo.empty and "annee" in df_evo.columns:
                fig = px.line(
                    df_evo, x="annee", y="count", color="filiere",
                    color_discrete_map=FILIERE_COLORS, markers=True,
                    labels={"annee": "Annee", "count": "Etudiants", "filiere": "Filiere"},
                )
                fig.update_layout(
                    height=300, margin=dict(t=20, b=20, l=20, r=20),
                    legend=dict(orientation="h", y=-0.3),
                    plot_bgcolor="white", paper_bgcolor="white",
                )
                fig.update_xaxes(gridcolor="#f0f0f0")
                fig.update_yaxes(gridcolor="#f0f0f0")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Donnees d'evolution non disponibles.")

    with g2:
        section_header("Repartition par filiere", annee)
        if by_filiere:
            df_fil = pd.DataFrame(by_filiere)
            fig2 = px.pie(
                df_fil, values="count", names="filiere",
                color="filiere", color_discrete_map=FILIERE_COLORS, hole=0.5,
            )
            fig2.update_layout(
                height=300, margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", y=-0.2), paper_bgcolor="white",
            )
            fig2.update_traces(textposition="outside", textinfo="percent+label")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Donnees non disponibles.")

    g3, g4 = st.columns([3, 2])

    with g3:
        section_header("Performance academique par departement")
        if success_data and abandon_data:
            sdf = pd.DataFrame(success_data)
            adf = pd.DataFrame(abandon_data)
            merged = sdf.merge(adf, on="filiere", how="outer").fillna(0)
            def statut(row):
                if row["taux_reussite_pct"] >= 80:  return "🟢 Excellent"
                elif row["taux_reussite_pct"] >= 70: return "🟡 Bon"
                elif row["taux_reussite_pct"] >= 60: return "🟠 Moyen"
                return "🔴 A surveiller"
            merged["statut"] = merged.apply(statut, axis=1)
            merged = merged.rename(columns={
                "filiere": "Departement",
                "total_notes": "Etudiants",
                "taux_reussite_pct": "Reussite %",
                "taux_abandon_pct": "Abandon %",
            })
            cols = [c for c in ["Departement", "Etudiants", "Reussite %", "Abandon %", "statut"] if c in merged.columns]
            st.dataframe(
                merged[cols].sort_values("Reussite %", ascending=False),
                hide_index=True, use_container_width=True, height=220,
            )
        else:
            st.info("Donnees academiques non disponibles.")

    with g4:
        section_header("Occupation des ressources")
        categories = ["Salles de cours", "Laboratoires", "Charge enseignants",
                      "Budget execute", "Diplomes / Objectif"]
        values = [87, 72, 91,
                  round(overview.get("taux_execution_budgetaire_pct", 84), 0),
                  round(overview.get("taux_reussite_global_pct", 78), 0)]
        colors = ["#2563EB", "#16a34a", "#dc2626", ENSA_GOLD, "#9333EA"]
        for cat, val, col in zip(categories, values, colors):
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"margin-bottom:0.4rem'>"
                f"<span style='font-size:0.82rem'>{cat}</span>"
                f"<span style='font-weight:700;color:{col};font-size:0.85rem'>{val:.0f}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.progress(int(min(val, 100)) / 100)

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;"
        "letter-spacing:0.08em'>PIPELINE ETL — STATUT</p>",
        unsafe_allow_html=True,
    )
    cols_etl = st.columns(4)
    items = [("Data Warehouse", "ok"), ("ETL actif", "ok"), ("OLAP sync", "ok"), ("Audit logs", "warn")]
    for col, (label, stat) in zip(cols_etl, items):
        with col:
            status_badge(label, stat)

st.markdown(
    f"""
    <div style='text-align:center;color:#9ca3af;font-size:0.75rem;margin-top:2rem;
                padding-top:1rem;border-top:1px solid #e5e7eb'>
    ENSA Kenitra — Architecture BI Securisee &nbsp;|&nbsp;
    AFTYSS Ilyass · ABDELMOUMEN Med Amine · BENHADDANE Anas &nbsp;|&nbsp; 2024-2025
    </div>
    """,
    unsafe_allow_html=True,
)