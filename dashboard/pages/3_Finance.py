"""
Page 3 — Analyse Financiere (direction/admin uniquement)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.auth_ui import require_auth, render_sidebar_nav
from dashboard.utils import api_get, section_header, apply_global_style, kpi_card, ANNEES, ENSA_BLUE, ENSA_GOLD

st.set_page_config(page_title="Finance | ENSA BI", layout="wide")

user = require_auth(allowed_roles=["administrateur", "direction"])
apply_global_style()
render_sidebar_nav()

with st.sidebar:
    st.markdown("---")
    annee = st.selectbox("Annee universitaire", ANNEES)
    toutes_annees = st.checkbox("Comparer toutes les annees", value=False)

st.title("💰 Analyse Financiere")
st.caption("Acces restreint — Direction et Administrateur")
st.markdown("---")

with st.spinner("Chargement..."):
    if toutes_annees:
        budget = api_get("/kpi/budget-usage") or {}
    else:
        budget = api_get("/kpi/budget-usage", {"annee_universitaire": annee}) or {}

taux_g = budget.get("taux_execution_global_pct", 0)
total_b = budget.get("total_budget", 0)
total_d = budget.get("total_depenses", 0)
ecart = total_b - total_d

c1, c2, c3, c4 = st.columns(4)
taux_color = "#16a34a" if taux_g >= 80 else "#d97706" if taux_g >= 60 else "#dc2626"
with c1: kpi_card("Execution", f"{taux_g:.1f}%", "Taux global", taux_color, "💹")
with c2: kpi_card("Budget total", f"{total_b/1e6:.1f}M MAD", "Alloue", ENSA_BLUE, "💰")
with c3: kpi_card("Depenses", f"{total_d/1e6:.1f}M MAD", "Consomme", ENSA_GOLD, "📤")
with c4:
    ecart_c = "#16a34a" if ecart >= 0 else "#dc2626"
    kpi_card("Solde", f"{ecart/1e6:.1f}M MAD", "Budget - Depenses", ecart_c, "🏦")

st.markdown("<br>", unsafe_allow_html=True)

par_dept = budget.get("par_departement", [])
if par_dept:
    df_f = pd.DataFrame(par_dept)
    df_f["ecart"] = df_f["budget"] - df_f["depenses"]
    df_f["anomalie"] = df_f["taux_pct"] > 100

    g1, g2 = st.columns(2)
    with g1:
        section_header("Budget vs Depenses par departement")
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Budget", x=df_f["departement"], y=df_f["budget"],
                              marker_color=ENSA_BLUE, text=df_f["budget"].apply(lambda v: f"{v/1e6:.1f}M"),
                              textposition="outside"))
        fig.add_trace(go.Bar(name="Depenses", x=df_f["departement"], y=df_f["depenses"],
                              marker_color=ENSA_GOLD, text=df_f["depenses"].apply(lambda v: f"{v/1e6:.1f}M"),
                              textposition="outside"))
        fig.update_layout(barmode="group", height=350,
                           margin=dict(t=10,b=80,l=10,r=10),
                           plot_bgcolor="white", paper_bgcolor="white",
                           xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        section_header("Taux d'execution par departement")
        fig2 = px.bar(
            df_f.sort_values("taux_pct"),
            x="taux_pct", y="departement", orientation="h",
            color="taux_pct",
            color_continuous_scale=["#dc2626", "#d97706", "#16a34a"],
            range_color=[0, 120],
            labels={"taux_pct": "Taux (%)", "departement": ""},
            text="taux_pct",
        )
        fig2.add_vline(x=100, line_dash="dash", line_color="#dc2626",
                       annotation_text="100%")
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.update_layout(height=350, margin=dict(t=10,b=10,l=10,r=80),
                            plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    section_header("Detail par departement")
    df_show = df_f[["departement","annee","budget","depenses","taux_pct","anomalie"]].copy()
    df_show.columns = ["Departement","Annee","Budget (MAD)","Depenses (MAD)","Taux %","Anomalie"]

    def color_anomalie(val):
        return "color: #dc2626; font-weight: bold;" if val else "color: #16a34a;"
    def color_taux(val):
        c = "#dc2626" if val > 100 else "#16a34a" if val >= 80 else "#d97706"
        return f"color: {c}; font-weight: bold;"

    st.dataframe(
        df_show.style
            .applymap(color_anomalie, subset=["Anomalie"])
            .applymap(color_taux, subset=["Taux %"]),
        hide_index=True, use_container_width=True,
    )
else:
    st.info("Donnees financieres non disponibles.")
