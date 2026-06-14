"""
Page 2 — Ressources (etudiant : emploi du temps | staff : ressources completes)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.auth_ui import require_auth, render_sidebar_nav
from dashboard.utils import api_get, section_header, apply_global_style, kpi_card, ANNEES, ENSA_BLUE

st.set_page_config(page_title="Ressources | ENSA BI", layout="wide")

user = require_auth(allowed_roles=["administrateur", "direction", "enseignant", "etudiant"])
apply_global_style()
render_sidebar_nav()

with st.sidebar:
    st.markdown("---")
    annee = st.selectbox("Annee universitaire", ANNEES)

role = user["role"]

# ── VUE ETUDIANT : Emploi du temps uniquement ─────────────────────────────────
if role == "etudiant":
    st.title("📅 Mon Emploi du Temps")
    st.caption(f"Sessions planifiees pour l'annee {annee}")
    st.markdown("---")

    with st.spinner("Chargement..."):
        mon_edt = api_get("/students/me/schedule", {"annee_universitaire": annee}) or []

    if not mon_edt:
        st.info(f"Aucun creneau trouve pour l'annee {annee}.")
    else:
        df_edt = pd.DataFrame(mon_edt)

        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Sessions", str(len(df_edt)), "Creneaux total", ENSA_BLUE, "📅")
        with c2:
            nb_salles = df_edt["salle"].nunique() if "salle" in df_edt.columns else 0
            kpi_card("Salles utilisees", str(nb_salles), "Differentes salles", "#7c3aed", "🏛")
        with c3:
            nb_cours = df_edt["cours"].nunique() if "cours" in df_edt.columns else 0
            kpi_card("Cours", str(nb_cours), "Matieres au programme", "#16a34a", "📖")

        st.markdown("<br>", unsafe_allow_html=True)

        g1, g2 = st.columns([2, 1])
        with g1:
            section_header("Planning complet")
            df_display = df_edt.copy()
            if "date" in df_display.columns:
                df_display["date"] = pd.to_datetime(df_display["date"], errors="coerce")
                df_display = df_display.sort_values(["date", "heure"])
            df_display = df_display.rename(columns={
                "date": "Date", "heure": "Heure", "cours": "Cours",
                "salle": "Salle", "type_salle": "Type", "semestre": "Sem.",
            })
            show_cols = [c for c in ["Date", "Heure", "Cours", "Salle", "Type", "Sem."]
                         if c in df_display.columns]
            st.dataframe(df_display[show_cols], hide_index=True, use_container_width=True, height=450)

        with g2:
            section_header("Sessions par cours")
            if "cours" in df_edt.columns:
                df_cnt = df_edt.groupby("cours").size().reset_index(name="sessions")
                fig = px.pie(
                    df_cnt, values="sessions", names="cours",
                    hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig.update_layout(height=400, margin=dict(t=10,b=10,l=10,r=10),
                                   paper_bgcolor="white",
                                   legend=dict(orientation="v", x=1.0))
                st.plotly_chart(fig, use_container_width=True)

    st.stop()

# ── VUE STAFF : Toutes les ressources ─────────────────────────────────────────
st.title("🏛 Occupation des Ressources")
st.markdown("---")

with st.spinner("Chargement..."):
    rooms    = api_get("/kpi/room-occupancy", {"annee_universitaire": annee}) or []
    workload = api_get("/kpi/teacher-workload") or []

if rooms:
    total_sessions = sum(r.get("nb_sessions", 0) for r in rooms)
    avg_occ = sum(r.get("taux_occupation_pct", 0) for r in rooms) / len(rooms)
    max_room = max(rooms, key=lambda r: r.get("taux_occupation_pct", 0), default={})
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total sessions", f"{total_sessions:,}", "", ENSA_BLUE, "📅")
    with c2: kpi_card("Taux moy.", f"{avg_occ:.1f}%", "Occupation", "#16a34a", "🏛")
    with c3: kpi_card("Salle +utilisee", max_room.get("salle","—"), f"{max_room.get('taux_occupation_pct',0):.0f}%", "#d97706", "🔥")
    with c4: kpi_card("Capacite max", f"{max(r.get('capacite',0) for r in rooms)} places", "", "#9333ea", "👥")

st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    section_header("Taux d'occupation par salle")
    if rooms:
        df_r = pd.DataFrame(rooms).sort_values("taux_occupation_pct", ascending=False).head(15)
        fig = px.bar(df_r, x="salle", y="taux_occupation_pct", color="type",
                     labels={"taux_occupation_pct": "Taux (%)", "salle": "", "type": "Type"},
                     text="taux_occupation_pct",)
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig.update_layout(height=350, margin=dict(t=10,b=80,l=10,r=10),
                           plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("Repartition par type")
    if rooms:
        df_type = pd.DataFrame(rooms).groupby("type")["nb_sessions"].sum().reset_index()
        fig2 = px.pie(df_type, values="nb_sessions", names="type", hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Set2,)
        fig2.update_layout(height=350, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

section_header("Charge des enseignants — Top 20")
if workload:
    df_w = pd.DataFrame(workload).head(20)
    fig4 = px.bar(df_w.sort_values("total_heures"),
                  x="total_heures", y="enseignant", orientation="h",
                  color="departement",
                  labels={"total_heures": "Heures totales", "enseignant": ""},
                  text="total_heures",)
    fig4.update_traces(textposition="outside")
    fig4.update_layout(height=500, margin=dict(t=10,b=10,l=10,r=60),
                        plot_bgcolor="white", paper_bgcolor="white",)
    st.plotly_chart(fig4, use_container_width=True)
