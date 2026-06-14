"""
auth_ui.py — Login page + RBAC sidebar.
Design: animated fluid gradient background + white card via st.container(border=True).
Tested with Streamlit 1.45.
"""
from __future__ import annotations
import streamlit as st
import requests
import os

API_URL   = os.getenv("API_URL", "http://localhost:8000")
ENSA_BLUE = "#1E3A5F"

ROLE_INFO = {
    "administrateur": {"color": "#dc2626", "label": "Administrateur"},
    "direction":      {"color": "#7c3aed", "label": "Direction"},
    "enseignant":     {"color": "#2563eb", "label": "Enseignant"},
    "etudiant":       {"color": "#16a34a", "label": "Etudiant"},
}

_GLOBAL_NAV_HIDE = """
<style>
[data-testid="stSidebarNav"] { display: none !important; }
</style>
"""

_LOGIN_CSS = """
<style>
/* ── Strip Streamlit chrome ── */
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"]  { display:none !important; }

/* ── Full-page dark background ── */
html,body { margin:0; padding:0; }
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] { background:#070f24 !important; }

/* ── Animated blobs ── */
@keyframes bA {
    0%,100%{ transform:translate(0,0) scale(1); }
    33%    { transform:translate(-65px,85px) scale(1.16); }
    66%    { transform:translate(85px,-45px) scale(0.87); }
}
@keyframes bB {
    0%,100%{ transform:translate(0,0) scale(1); }
    25%    { transform:translate(95px,-75px) scale(1.13); }
    75%    { transform:translate(-55px,65px) scale(0.91); }
}
@keyframes bC {
    0%,100%{ transform:translate(0,0) scale(1); }
    50%    { transform:translate(-75px,-85px) scale(1.2); }
}
@keyframes bD {
    0%,100%{ transform:translate(0,0) scale(1); }
    40%    { transform:translate(65px,55px) scale(0.87); }
    80%    { transform:translate(-35px,-65px) scale(1.11); }
}
.bwrap{position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:0;}
.blob{position:absolute;border-radius:50%;filter:blur(100px);will-change:transform;}
.b1{width:680px;height:680px;
    background:radial-gradient(circle at 40% 40%,#d4ab6a,#e8c97a 45%,transparent 70%);
    top:-200px;right:-80px;opacity:.55;animation:bA 14s ease-in-out infinite;}
.b2{width:500px;height:500px;
    background:radial-gradient(circle at 50% 50%,#4a8fd9,#1a5bab 55%,transparent 75%);
    bottom:-120px;left:-60px;opacity:.6;animation:bB 18s ease-in-out infinite;}
.b3{width:420px;height:420px;
    background:radial-gradient(circle at 50% 50%,#c4b5fd,#8b5cf6 55%,transparent 75%);
    top:38%;left:52%;opacity:.32;animation:bC 12s ease-in-out infinite;}
.b4{width:320px;height:320px;
    background:radial-gradient(circle at 50% 50%,#fde68a,#f59e0b 55%,transparent 75%);
    bottom:8%;right:12%;opacity:.28;animation:bD 16s ease-in-out infinite;}

/* ── Center the content block ── */
.main .block-container{
    max-width:480px !important;
    padding:4vh 1rem !important;
    margin:0 auto !important;
    position:relative; z-index:10;
}

/* ── White card: the border container ── */
[data-testid="stVerticalBlockBorderWrapper"]{
    background:rgba(255,255,255,0.97) !important;
    border:none !important;
    border-radius:20px !important;
    padding:2.6rem 2.6rem 2rem !important;
    box-shadow:0 4px 6px rgba(0,0,0,.05),
               0 16px 40px rgba(0,0,0,.18),
               0 40px 80px rgba(0,0,0,.40) !important;
}

/* ── Input fields ── */
[data-testid="stTextInput"] input{
    border:1.5px solid #e2e8f0 !important;
    border-radius:9px !important;
    padding:.65rem 1rem !important;
    font-size:.94rem !important;
    background:#f8fafc !important;
    color:#111827 !important;
    transition:border-color .18s,box-shadow .18s,background .18s;
}
[data-testid="stTextInput"] input:focus{
    border-color:#1E3A5F !important;
    box-shadow:0 0 0 3px rgba(30,58,95,.13) !important;
    background:#fff !important;
    outline:none !important;
}
[data-testid="stTextInput"] label{
    font-size:.72rem !important;font-weight:700 !important;
    letter-spacing:.09em !important;text-transform:uppercase !important;
    color:#6b7280 !important;
}

/* ── Submit button ── */
[data-testid="stFormSubmitButton"]>button{
    background:#1E3A5F !important;color:#fff !important;
    border:none !important;border-radius:9px !important;
    padding:.72rem 1.5rem !important;
    font-size:.92rem !important;font-weight:700 !important;
    letter-spacing:.04em !important;width:100% !important;
    transition:background .18s,transform .12s,box-shadow .18s !important;
    cursor:pointer;
}
[data-testid="stFormSubmitButton"]>button:hover{
    background:#152d4a !important;
    transform:translateY(-1px) !important;
    box-shadow:0 8px 20px rgba(30,58,95,.32) !important;
}
[data-testid="stFormSubmitButton"]>button:active{ transform:translateY(0) !important; }

/* ── Misc ── */
[data-testid="stAlert"]   { border-radius:9px !important; font-size:.87rem !important; }
[data-testid="stExpander"]{ border:1px solid #e5e7eb !important; border-radius:9px !important; }
[data-testid="stExpander"] summary{ font-size:.82rem !important; color:#4b5563 !important; }
</style>

<div class="bwrap">
    <div class="blob b1"></div>
    <div class="blob b2"></div>
    <div class="blob b3"></div>
    <div class="blob b4"></div>
</div>
"""


def _login_request(username: str, password: str) -> dict | None:
    try:
        r = requests.post(
            f"{API_URL}/auth/token",
            data={"username": username, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()
        return {"error": r.json().get("detail", "Identifiants incorrects")}
    except requests.exceptions.ConnectionError:
        return {"error": "API non disponible. Verifiez que le serveur FastAPI est demarre (port 8000)."}
    except Exception as e:
        return {"error": str(e)}


def render_login_page():
    """Page de connexion — fond anime, card blanche via st.container(border=True)."""
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    with st.container(border=True):

        # ── Branding ──────────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="margin-bottom:1.8rem;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.4rem;">
                <div style="width:34px;height:34px;border-radius:8px;background:{ENSA_BLUE};
                            display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                         stroke="white" stroke-width="2.5"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <span style="font-size:.93rem;font-weight:800;color:{ENSA_BLUE};
                             letter-spacing:-.1px;">ENSA Kenitra</span>
            </div>
            <h2 style="font-size:1.9rem;font-weight:900;color:#0f172a;
                       margin:0 0 .35rem;letter-spacing:-.5px;line-height:1.1;">
                Connexion
            </h2>
            <p style="color:#64748b;font-size:.86rem;margin:0;">
                Acces a votre espace Business Intelligence
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Form ──────────────────────────────────────────────────────────────
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Identifiant", placeholder="admin, direction, prenom.nom...")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "Se connecter",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not username or not password:
                st.warning("Veuillez saisir vos identifiants.")
            else:
                with st.spinner("Verification..."):
                    result = _login_request(username.strip(), password)
                if result and "error" not in result:
                    st.session_state.update({
                        "authenticated": True,
                        "token":         result["access_token"],
                        "role":          result["role"],
                        "full_name":     result["full_name"],
                        "username":      result["username"],
                    })
                    try:
                        me = requests.get(
                            f"{API_URL}/auth/me",
                            headers={"Authorization": f"Bearer {result['access_token']}"},
                            timeout=5,
                        ).json()
                        st.session_state["student_id"]  = me.get("student_id")
                        st.session_state["teacher_id"]  = me.get("teacher_id")
                        st.session_state["permissions"] = me.get("permissions", {})
                    except Exception:
                        st.session_state["student_id"]  = None
                        st.session_state["teacher_id"]  = None
                        st.session_state["permissions"] = {}
                    st.rerun()
                else:
                    err = result.get("error", "Erreur inconnue") if result else "Serveur API non disponible"
                    st.error(err)

        # ── Divider ───────────────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin:1rem 0 .9rem;">
            <div style="flex:1;height:1px;background:#e5e7eb;"></div>
            <span style="color:#9ca3af;font-size:.69rem;font-weight:600;
                         letter-spacing:.09em;text-transform:uppercase;">Demo</span>
            <div style="flex:1;height:1px;background:#e5e7eb;"></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Demo credentials ──────────────────────────────────────────────────
        with st.expander("Identifiants de demonstration", expanded=False):
            st.markdown("""
            <table style="width:100%;border-collapse:collapse;font-size:.79rem;color:#374151;">
              <thead>
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <th style="padding:4px 8px;text-align:left;font-size:.67rem;
                             color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;">Role</th>
                  <th style="padding:4px 8px;text-align:left;font-size:.67rem;
                             color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;">Login</th>
                  <th style="padding:4px 8px;text-align:left;font-size:.67rem;
                             color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;">Mot de passe</th>
                </tr>
              </thead>
              <tbody>
                <tr><td style="padding:5px 8px;">Administrateur</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#1E3A5F;">admin</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#1E3A5F;">Admin@ENSA2025</td></tr>
                <tr style="background:#f9fafb;">
                    <td style="padding:5px 8px;">Direction</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#1E3A5F;">direction</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#1E3A5F;">Direction@ENSA2025</td></tr>
                <tr><td style="padding:5px 8px;">Enseignant</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#6b7280;">prenom.nom</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#6b7280;">Enseignant_&lt;id&gt;</td></tr>
                <tr style="background:#f9fafb;">
                    <td style="padding:5px 8px;">Etudiant</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#6b7280;">email@...</td>
                    <td style="padding:5px 8px;font-family:monospace;color:#6b7280;">Etudiant_&lt;id&gt;</td></tr>
              </tbody>
            </table>
            """, unsafe_allow_html=True)

        st.markdown("""
        <p style="text-align:center;color:#9ca3af;font-size:.68rem;margin-top:1.2rem;">
            AFTYSS &nbsp;&middot;&nbsp; ABDELMOUMEN &nbsp;&middot;&nbsp; BENHADDANE
            &nbsp;&mdash;&nbsp; 2024-2025
        </p>
        """, unsafe_allow_html=True)

    st.stop()


def require_auth(allowed_roles: list[str] | None = None):
    if not st.session_state.get("authenticated"):
        render_login_page()
    role = st.session_state.get("role")
    if allowed_roles and role not in allowed_roles:
        st.markdown(_GLOBAL_NAV_HIDE, unsafe_allow_html=True)
        st.error("Acces refuse. Cette page n'est pas disponible pour votre role.")
        st.info("Utilisez la navigation pour aller sur une page accessible.")
        if st.button("Retour accueil"):
            st.switch_page("streamlit_app.py")
        st.stop()
    return {
        "username":    st.session_state.get("username", ""),
        "full_name":   st.session_state.get("full_name", ""),
        "role":        role,
        "student_id":  st.session_state.get("student_id"),
        "teacher_id":  st.session_state.get("teacher_id"),
        "permissions": st.session_state.get("permissions", {}),
    }


def render_sidebar_nav():
    st.markdown(_GLOBAL_NAV_HIDE, unsafe_allow_html=True)
    role      = st.session_state.get("role", "")
    full_name = st.session_state.get("full_name", "Utilisateur")
    role_info = ROLE_INFO.get(role, {"color": "#64748b", "label": role.capitalize()})

    with st.sidebar:
        initials = "".join(w[0].upper() for w in full_name.split()[:2]) or "?"
        st.markdown(f"""
        <div style="padding:1.2rem 0 1rem;text-align:center;">
            <div style="width:50px;height:50px;border-radius:50%;
                        background:{role_info['color']};display:flex;
                        align-items:center;justify-content:center;
                        margin:0 auto .6rem;font-weight:800;font-size:1rem;
                        color:white;letter-spacing:1px;">{initials}</div>
            <div style="font-weight:700;font-size:.9rem;color:white;
                        overflow:hidden;text-overflow:ellipsis;
                        white-space:nowrap;max-width:170px;margin:0 auto;">
                {full_name}</div>
            <div style="margin-top:5px;">
                <span style="background:rgba(255,255,255,.15);color:white;
                             padding:2px 10px;border-radius:20px;
                             font-size:.67rem;font-weight:700;letter-spacing:.06em;">
                    {role_info['label'].upper()}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,.12);margin:0 0 .8rem'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='font-size:.66rem;font-weight:700;letter-spacing:.12em;"
            "color:rgba(255,255,255,.4);text-transform:uppercase;"
            "margin:0 0 .4rem;padding:0 .2rem'>Navigation</p>",
            unsafe_allow_html=True,
        )

        if role == "etudiant":
            st.page_link("streamlit_app.py",          label="Accueil")
            st.page_link("pages/0_Mon_Espace.py",     label="Mon Espace")
            st.page_link("pages/2_Ressources.py",     label="Mon Emploi du Temps")
        elif role == "enseignant":
            st.page_link("streamlit_app.py",                   label="Tableau de bord")
            st.page_link("pages/1_Performance_Academique.py",  label="Mes Cours")
            st.page_link("pages/2_Ressources.py",              label="Ressources")
        elif role in ("direction", "administrateur"):
            st.page_link("streamlit_app.py",                   label="Vue Generale")
            st.page_link("pages/1_Performance_Academique.py",  label="Performance Academique")
            st.page_link("pages/2_Ressources.py",              label="Ressources")
            st.page_link("pages/3_Finance.py",                 label="Finance")
            st.page_link("pages/4_RH.py",                      label="Ressources Humaines")

        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,.12);margin:.6rem 0 .5rem'>",
            unsafe_allow_html=True,
        )
        if st.button("Se deconnecter", use_container_width=True):
            for key in ["authenticated", "token", "role", "full_name",
                        "username", "student_id", "teacher_id", "permissions"]:
                st.session_state.pop(key, None)
            st.rerun()
