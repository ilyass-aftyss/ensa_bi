"""
Page 0 — Mon Espace (Etudiant)
Vue personnalisee pour chaque etudiant : profil, notes, emploi du temps.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.auth_ui import require_auth, render_sidebar_nav
from dashboard.utils import api_get, section_header, apply_global_style, kpi_card, ANNEES, ENSA_BLUE, ENSA_GOLD

st.set_page_config(page_title="Mon Espace | ENSA BI", page_icon="🎓", layout="wide")

user = require_auth(allowed_roles=["etudiant", "administrateur"])
apply_global_style()
render_sidebar_nav()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    annee = st.selectbox("Annee universitaire", ANNEES, index=0)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='margin-bottom:0'>🎓 Mon Espace</h1>"
    f"<p style='color:#6b7280;font-size:0.9rem'>Tableau de bord personnel &nbsp;|&nbsp; "
    f"<span style='color:#16a34a;font-weight:600'>● {user['full_name']}</span></p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Chargement donnees ────────────────────────────────────────────────────────
with st.spinner("Chargement de vos donnees..."):
    profil      = api_get("/students/me") or {}
    mes_notes   = api_get("/students/me/grades", {"annee_universitaire": annee}) or []
    mon_edt     = api_get("/students/me/schedule", {"annee_universitaire": annee}) or []
    mes_inscr   = api_get("/students/me/enrollments") or []

# ── Profil card ───────────────────────────────────────────────────────────────
col_profil, col_stats = st.columns([1, 2])

with col_profil:
    section_header("Mon Profil")
    if profil:
        sexe_icon = "👨" if profil.get("sexe") == "M" else "👩" if profil.get("sexe") == "F" else "👤"
        st.markdown(f"""
        <div style='background:white;border-radius:14px;padding:1.5rem;
                    box-shadow:0 2px 10px rgba(0,0,0,0.08);border-top:4px solid {ENSA_BLUE};'>
            <div style='text-align:center;margin-bottom:1rem;'>
                <div style='font-size:3rem;'>{sexe_icon}</div>
                <div style='font-weight:800;font-size:1.1rem;color:{ENSA_BLUE};'>
                    {profil.get("prenom","")} {profil.get("nom","")}
                </div>
                <div style='color:#64748b;font-size:0.82rem;margin-top:2px;'>
                    {profil.get("email","")}
                </div>
            </div>
            <hr style='border:none;border-top:1px solid #e5e7eb;margin:0.8rem 0;'>
            <table style='width:100%;font-size:0.83rem;'>
                <tr><td style='color:#6b7280;padding:3px 0;'>Filiere</td>
                    <td style='font-weight:600;'>{profil.get("filiere","—")}</td></tr>
                <tr><td style='color:#6b7280;padding:3px 0;'>Annee cursus</td>
                    <td style='font-weight:600;'>Annee {profil.get("annee_cursus","—")}</td></tr>
                <tr><td style='color:#6b7280;padding:3px 0;'>Annee entree</td>
                    <td style='font-weight:600;'>{profil.get("annee_entree","—")}</td></tr>
                <tr><td style='color:#6b7280;padding:3px 0;'>Ville</td>
                    <td style='font-weight:600;'>{profil.get("ville_origine","—")}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Profil non disponible.")

with col_stats:
    section_header(f"Mes resultats — {annee}")
    if mes_notes:
        df_n = pd.DataFrame(mes_notes)
        avg = df_n["note"].mean()
        nb_cours = len(df_n)
        nb_reussi = (df_n["note"] >= 10).sum()
        taux_r = nb_reussi / nb_cours * 100 if nb_cours else 0
        meilleure = df_n.loc[df_n["note"].idxmax(), "cours"] if not df_n.empty else "—"

        kc1, kc2, kc3 = st.columns(3)
        with kc1: kpi_card("Moyenne", f"{avg:.2f}/20", f"{nb_cours} cours", ENSA_BLUE, "📊")
        with kc2:
            c = "#16a34a" if taux_r >= 70 else "#d97706" if taux_r >= 50 else "#dc2626"
            kpi_card("Reussite", f"{taux_r:.0f}%", f"{nb_reussi}/{nb_cours} cours", c, "🏆")
        with kc3: kpi_card("Meilleure note", f"{df_n['note'].max():.1f}/20", meilleure[:25]+"..." if len(meilleure)>25 else meilleure, ENSA_GOLD, "⭐")

        st.markdown("<br>", unsafe_allow_html=True)

        # Graphique notes par cours
        fig = px.bar(
            df_n.sort_values("note", ascending=True),
            x="note", y="cours", orientation="h",
            color="note",
            color_continuous_scale=["#dc2626", "#d97706", "#16a34a"],
            range_color=[0, 20],
            labels={"note": "Note /20", "cours": "Cours"},
            text="note",
        )
        fig.add_vline(x=10, line_dash="dash", line_color="#64748b",
                      annotation_text="Seuil 10", annotation_position="top right")
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(
            height=280 + len(df_n) * 10,
            margin=dict(t=10, b=10, l=10, r=80),
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Aucune note disponible pour l'annee {annee}.")

# ── Notes detaillees ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
tab_notes, tab_edt, tab_parcours = st.tabs(["📝 Releve de Notes", "📅 Emploi du Temps", "📋 Parcours"])

with tab_notes:
    if mes_notes:
        df_n = pd.DataFrame(mes_notes)

        MENTION_COLORS = {
            "Tres bien":  "#16a34a",
            "Bien":       "#2563eb",
            "Assez bien": "#7c3aed",
            "Passable":   "#d97706",
            "Insuffisant":"#dc2626",
        }

        def color_note(val):
            if isinstance(val, float):
                c = "#16a34a" if val >= 14 else "#2563eb" if val >= 12 else "#d97706" if val >= 10 else "#dc2626"
                return f"color: {c}; font-weight: bold;"
            return ""

        df_display = df_n.rename(columns={
            "cours": "Cours",
            "note": "Note /20",
            "semestre": "Semestre",
            "annee_universitaire": "Annee",
            "mention": "Mention",
        })
        st.dataframe(
            df_display[["Cours", "Note /20", "Semestre", "Annee", "Mention"]].style.applymap(
                color_note, subset=["Note /20"]
            ),
            hide_index=True,
            use_container_width=True,
            height=350,
        )

        # Comparaison par semestre
        if "semestre" in df_n.columns:
            df_sem = df_n.groupby("semestre")["note"].agg(["mean", "min", "max"]).reset_index()
            df_sem.columns = ["Semestre", "Moyenne", "Min", "Max"]
            section_header("Performance par semestre")
            fig_s = px.bar(df_sem, x="Semestre", y="Moyenne",
                           color="Moyenne",
                           color_continuous_scale=["#dc2626", "#d97706", "#16a34a"],
                           range_color=[0, 20],
                           labels={"Semestre": "Semestre", "Moyenne": "Moyenne /20"},
                           text="Moyenne",)
            fig_s.add_hline(y=10, line_dash="dash", line_color="#64748b")
            fig_s.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_s.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10),
                                 plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig_s, use_container_width=True)
    else:
        st.info("Aucune note disponible.")

with tab_edt:
    section_header(f"Emploi du temps — {annee}")
    if mon_edt:
        df_edt = pd.DataFrame(mon_edt)
        df_edt["date"] = pd.to_datetime(df_edt["date"], errors="coerce")
        df_edt_display = df_edt.rename(columns={
            "date": "Date",
            "heure": "Heure",
            "cours": "Cours",
            "semestre": "Semestre",
            "salle": "Salle",
            "type_salle": "Type salle",
        }).sort_values(["Date", "Heure"])

        cols_show = [c for c in ["Date", "Heure", "Cours", "Semestre", "Salle", "Type salle"]
                     if c in df_edt_display.columns]
        st.dataframe(df_edt_display[cols_show], hide_index=True, use_container_width=True, height=400)

        # Graphique sessions par cours
        if "cours" in df_edt.columns:
            df_count = df_edt.groupby("cours").size().reset_index(name="sessions")
            fig_e = px.bar(
                df_count.sort_values("sessions", ascending=False),
                x="cours", y="sessions",
                labels={"cours": "Cours", "sessions": "Nb sessions"},
                color="sessions",
                color_continuous_scale="Blues",
                text="sessions",
            )
            fig_e.update_traces(textposition="outside")
            fig_e.update_layout(height=280, margin=dict(t=10, b=80, l=10, r=10),
                                  plot_bgcolor="white", paper_bgcolor="white",
                                  showlegend=False, xaxis_tickangle=-30)
            st.plotly_chart(fig_e, use_container_width=True)
    else:
        st.info(f"Aucun creneau trouve pour l'annee {annee}.")

with tab_parcours:
    section_header("Historique des inscriptions")
    if mes_inscr:
        df_i = pd.DataFrame(mes_inscr).rename(columns={
            "annee_universitaire": "Annee",
            "filiere": "Filiere",
            "statut": "Statut",
            "annee_cursus": "Annee de cursus",
        })
        STATUT_COLORS = {"inscrit": "#16a34a", "diplome": "#2563eb", "abandonne": "#dc2626"}

        def style_statut(val):
            c = STATUT_COLORS.get(str(val).lower(), "#64748b")
            return f"color: {c}; font-weight: 600;"

        st.dataframe(
            df_i.style.applymap(style_statut, subset=["Statut"]),
            hide_index=True, use_container_width=True,
        )
    else:
        st.info("Aucune inscription trouvee.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#9ca3af;font-size:0.75rem;margin-top:2rem;"
    "padding-top:1rem;border-top:1px solid #e5e7eb'>"
    "ENSA Kenitra — BI Securisee | 2024-2025 | AFTYSS · ABDELMOUMEN · BENHADDANE"
    "</div>",
    unsafe_allow_html=True,
)
