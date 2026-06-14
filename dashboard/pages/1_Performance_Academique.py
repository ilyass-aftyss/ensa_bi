"""
Page 1 — Performance Academique (staff + enseignant filtre)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.auth_ui import require_auth, render_sidebar_nav
from dashboard.utils import api_get, section_header, apply_global_style, ANNEES, FILIERE_COLORS, ENSA_BLUE, kpi_card

st.set_page_config(page_title="Performance Academique | ENSA BI", layout="wide")

user = require_auth(allowed_roles=["administrateur", "direction", "enseignant"])
apply_global_style()
render_sidebar_nav()

with st.sidebar:
    st.markdown("---")
    annee = st.selectbox("Annee universitaire", ANNEES)

role = user["role"]

if role == "enseignant":
    st.title("📊 Performance — Mes Cours")
    st.caption(f"Donnees de l'annee {annee} — Vue enseignant")
    st.markdown("---")
    with st.spinner("Chargement..."):
        my_perf  = api_get("/teachers/me/students-performance", {"annee_universitaire": annee}) or []
        my_cours = api_get("/teachers/me/courses") or []

    if not my_perf:
        st.info("Aucune donnee de performance disponible pour cette annee.")
    else:
        c1, c2, c3 = st.columns(3)
        avg_global = sum(p.get("moyenne", 0) for p in my_perf) / len(my_perf) if my_perf else 0
        avg_reussite = sum(p.get("taux_reussite_pct", 0) for p in my_perf) / len(my_perf) if my_perf else 0
        total_notes = sum(p.get("nb_notes", 0) for p in my_perf)
        with c1: kpi_card("Cours evalues", str(len(my_perf)), "Avec notes", ENSA_BLUE, "📖")
        with c2: kpi_card("Moyenne globale", f"{avg_global:.2f}/20", "Vos cours", "#2563eb", "📊")
        with c3: kpi_card("Taux reussite", f"{avg_reussite:.1f}%", f"{total_notes} notes", "#16a34a", "🏆")

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            section_header("Performance par cours")
            df_p = pd.DataFrame(my_perf)
            fig = px.bar(
                df_p.sort_values("taux_reussite_pct"),
                x="taux_reussite_pct", y="cours", orientation="h",
                color="taux_reussite_pct",
                color_continuous_scale=["#dc2626", "#d97706", "#16a34a"],
                range_color=[0, 100],
                labels={"taux_reussite_pct": "Taux reussite (%)", "cours": ""},
                text="taux_reussite_pct",
            )
            fig.add_vline(x=50, line_dash="dash", line_color="#64748b")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(height=350, margin=dict(t=10,b=10,l=10,r=80),
                               plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            section_header("Moyenne par cours")
            df_p2 = pd.DataFrame(my_perf)
            fig2 = px.scatter(
                df_p2, x="moyenne", y="cours",
                size="nb_notes", color="taux_reussite_pct",
                color_continuous_scale=["#dc2626", "#d97706", "#16a34a"],
                range_color=[0, 100],
                labels={"moyenne": "Moyenne /20", "cours": "", "nb_notes": "Nb notes"},
                size_max=30,
            )
            fig2.add_vline(x=10, line_dash="dash", line_color="#64748b")
            fig2.update_layout(height=350, margin=dict(t=10,b=10,l=10,r=10),
                                plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)

        section_header("Detail par cours")
        df_detail = pd.DataFrame(my_perf).rename(columns={
            "cours": "Cours", "nb_notes": "Notes", "moyenne": "Moyenne /20",
            "taux_reussite_pct": "Reussite %",
        })
        st.dataframe(df_detail, hide_index=True, use_container_width=True)

else:
    # Direction / Admin
    st.title("📊 Performance Academique")
    st.caption(f"Donnees pour l'annee {annee}")
    st.markdown("---")

    with st.spinner("Chargement..."):
        success = api_get("/kpi/success-rate", {"annee_universitaire": annee}) or []
        abandon = api_get("/kpi/abandon-rate", {"annee_universitaire": annee}) or []
        avg     = api_get("/kpi/avg-grade", {"annee_universitaire": annee}) or {}
        tops    = api_get("/kpi/top-filieres", {"annee_universitaire": annee}) or []

    c1, c2, c3, c4 = st.columns(4)
    global_avg = avg.get("moyenne_globale", 0)
    best = success[0] if success else {}
    worst = success[-1] if success else {}
    total_n = sum(s.get("total_notes", 0) for s in success)

    with c1: kpi_card("Moyenne globale", f"{global_avg:.2f}/20", f"Annee {annee}", ENSA_BLUE, "📊")
    with c2: kpi_card("Meilleure filiere", best.get("filiere", "—"), f"{best.get('taux_reussite_pct',0):.1f}% reussite", "#16a34a", "🏆")
    with c3: kpi_card("Filiere a surveiller", worst.get("filiere", "—"), f"{worst.get('taux_reussite_pct',0):.1f}% reussite", "#dc2626", "⚠️")
    with c4: kpi_card("Total notes", f"{total_n:,}", "Evaluations", "#7c3aed", "📝")

    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)

    with g1:
        section_header("Taux de reussite par filiere")
        if success:
            df_s = pd.DataFrame(success)
            fig = px.bar(
                df_s, x="filiere", y="taux_reussite_pct",
                color="taux_reussite_pct",
                color_continuous_scale=["#dc2626", "#d97706", "#16a34a"],
                range_color=[0, 100],
                labels={"filiere": "Filiere", "taux_reussite_pct": "Taux (%)"},
                text="taux_reussite_pct",
            )
            fig.add_hline(y=50, line_dash="dash", line_color="#64748b",
                          annotation_text="Seuil 50%")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(height=320, margin=dict(t=10,b=40,l=10,r=10),
                               plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with g2:
        section_header("Moyenne par filiere")
        if avg.get("par_filiere"):
            df_a = pd.DataFrame(avg["par_filiere"])
            fig2 = px.bar(
                df_a.sort_values("moyenne", ascending=False),
                x="filiere", y="moyenne",
                color="filiere", color_discrete_map=FILIERE_COLORS,
                labels={"filiere": "", "moyenne": "Moyenne /20"},
                text="moyenne",
            )
            fig2.add_hline(y=10, line_dash="dash", line_color="#64748b")
            fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig2.update_layout(height=320, margin=dict(t=10,b=40,l=10,r=10),
                                plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    section_header("Classement des filieres")
    if tops:
        df_t = pd.DataFrame(tops)
        df_t["Statut"] = df_t["moyenne"].apply(
            lambda m: "🟢 Excellent" if m >= 14 else "🟡 Bon" if m >= 12 else "🟠 Moyen" if m >= 10 else "🔴 Insuffisant"
        )
        df_t.columns = [c.replace("rank","Rang").replace("filiere","Filiere")
                        .replace("moyenne","Moyenne /20").replace("nb_etudiants","Etudiants") for c in df_t.columns]
        st.dataframe(df_t, hide_index=True, use_container_width=True)
