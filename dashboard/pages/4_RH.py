"""
Page 4 — Ressources Humaines & Etudiants (direction/admin uniquement)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.auth_ui import require_auth, render_sidebar_nav
from dashboard.utils import api_get, section_header, apply_global_style, kpi_card, ANNEES, ENSA_BLUE, FILIERE_COLORS

st.set_page_config(page_title="Ressources Humaines | ENSA BI", layout="wide")

user = require_auth(allowed_roles=["administrateur", "direction"])
apply_global_style()
render_sidebar_nav()

with st.sidebar:
    st.markdown("---")
    annee = st.selectbox("Annee universitaire", ANNEES)

st.title("👥 Ressources Humaines & Etudiants")
st.caption("Acces restreint — Direction et Administrateur")
st.markdown("---")

with st.spinner("Chargement..."):
    count_data  = api_get("/students/count") or {}
    by_filiere  = api_get("/students/by-filiere") or []
    evolution   = api_get("/students/evolution") or []
    workload    = api_get("/kpi/teacher-workload") or []
    enr_summary = api_get("/kpi/enrollments-summary", {"annee_universitaire": annee}) or {}

total_etudiants = count_data.get("total", 0)
nb_inscrits   = enr_summary.get("inscrit", 0)
nb_diplomes   = enr_summary.get("diplome", 0)
nb_abandonnes = enr_summary.get("abandonne", 0)
total_enr = nb_inscrits + nb_diplomes + nb_abandonnes or 1

c1, c2, c3, c4 = st.columns(4)
with c1: kpi_card("Effectif total", f"{total_etudiants:,}", "Etudiants", ENSA_BLUE, "👥")
with c2: kpi_card("Inscrits", f"{nb_inscrits:,}", f"Annee {annee}", "#16a34a", "✅")
with c3: kpi_card("Diplomes", f"{nb_diplomes:,}", f"Annee {annee}", "#2563eb", "🎓")
with c4:
    taux_a = nb_abandonnes / total_enr * 100
    ca = "#dc2626" if taux_a > 8 else "#d97706" if taux_a > 5 else "#16a34a"
    kpi_card("Abandons", f"{nb_abandonnes:,}", f"{taux_a:.1f}% taux", ca, "📉")

st.markdown("<br>", unsafe_allow_html=True)
g1, g2 = st.columns(2)

with g1:
    section_header("Evolution des inscriptions par filiere")
    if evolution:
        df_evo = pd.DataFrame(evolution)
        fig = px.line(df_evo, x="annee", y="count", color="filiere",
                      color_discrete_map=FILIERE_COLORS, markers=True,
                      labels={"annee": "Annee", "count": "Etudiants", "filiere": "Filiere"})
        fig.update_layout(height=320, margin=dict(t=10,b=20,l=10,r=10),
                           plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, use_container_width=True)

with g2:
    section_header("Repartition par filiere")
    if by_filiere:
        df_fil = pd.DataFrame(by_filiere)
        fig2 = px.pie(df_fil, values="count", names="filiere", color="filiere",
                      color_discrete_map=FILIERE_COLORS, hole=0.45)
        fig2.update_layout(height=320, margin=dict(t=10,b=10,l=10,r=10),
                            paper_bgcolor="white",
                            legend=dict(orientation="h", y=-0.15))
        fig2.update_traces(textposition="outside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

section_header("Statut des inscriptions — " + annee)
if enr_summary:
    df_enr = pd.DataFrame([
        {"Statut": "Inscrits",    "Nombre": nb_inscrits,   "Couleur": "#16a34a"},
        {"Statut": "Diplomes",    "Nombre": nb_diplomes,   "Couleur": "#2563eb"},
        {"Statut": "Abandonnes",  "Nombre": nb_abandonnes, "Couleur": "#dc2626"},
    ])
    fig3 = px.bar(df_enr, x="Statut", y="Nombre", color="Statut",
                  color_discrete_map={"Inscrits": "#16a34a", "Diplomes": "#2563eb", "Abandonnes": "#dc2626"},
                  text="Nombre",)
    fig3.update_traces(textposition="outside")
    fig3.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10),
                        plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

section_header("Charge des enseignants")
if workload:
    df_w = pd.DataFrame(workload)
    g3, g4 = st.columns(2)
    with g3:
        fig4 = px.bar(
            df_w.head(15).sort_values("total_heures"),
            x="total_heures", y="enseignant", orientation="h",
            color="departement",
            labels={"total_heures": "Heures totales", "enseignant": ""},
            text="total_heures",
        )
        fig4.update_traces(textposition="outside")
        fig4.update_layout(height=420, margin=dict(t=10,b=10,l=10,r=60),
                            plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig4, use_container_width=True)
    with g4:
        df_dept = df_w.groupby("departement").agg(
            nb_ens=("enseignant","count"), total_h=("total_heures","sum")
        ).reset_index()
        fig5 = px.pie(df_dept, values="total_h", names="departement",
                      hole=0.4, title="Heures par departement",
                      color_discrete_sequence=px.colors.qualitative.Set1)
        fig5.update_layout(height=420, paper_bgcolor="white")
        st.plotly_chart(fig5, use_container_width=True)
