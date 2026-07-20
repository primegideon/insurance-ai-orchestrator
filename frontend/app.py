"""
Insurance AI Orchestrator – Streamlit frontend
Connects to the FastAPI backend at http://localhost:8000
"""

import os
import streamlit as st
import requests
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Page config  ── must be FIRST Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Insurance AI Risk Underwriter",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------
def _get_secret(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        try:
            value = st.secrets[key]
        except (KeyError, FileNotFoundError):
            value = ""
    return value or ""

_SUPABASE_URL = _get_secret("SUPABASE_URL")
_SUPABASE_KEY = _get_secret("SUPABASE_KEY")

@st.cache_resource
def _get_supabase_client() -> Client:
    return create_client(_SUPABASE_URL, _SUPABASE_KEY)

supabase: Client = _get_supabase_client()

# ---------------------------------------------------------------------------
# Common ICD-10 codes and medical flags for multiselect dropdowns
# ---------------------------------------------------------------------------
ICD10_OPTIONS = [
    "I21.9 — Acute Myocardial Infarction",
    "I10   — Essential Hypertension",
    "E11   — Type 2 Diabetes",
    "C34   — Lung Cancer",
    "J45   — Asthma",
    "I63   — Cerebral Infarction (Stroke)",
    "K70   — Alcoholic Liver Disease",
    "F20   — Schizophrenia",
    "G30   — Alzheimer's Disease",
    "N18   — Chronic Kidney Disease",
]

MEDICAL_FLAG_OPTIONS = [
    "Hypertension",
    "Type 2 Diabetes",
    "Smoker",
    "Obesity (BMI > 30)",
    "Heart Disease",
    "Stroke History",
    "Cancer (any)",
    "Chronic Kidney Disease",
    "Asthma / COPD",
    "Mental Health Disorder",
    "HIV / AIDS",
    "Liver Cirrhosis",
]

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── Hide Streamlit chrome ── */
    #MainMenu  { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }

    /* ── Global typography ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }

    /* ── Full-page backdrop ── */
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 10% 0%,   rgba(0,114,198,0.22) 0%, transparent 55%),
            radial-gradient(ellipse at 90% 5%,   rgba(0,174,239,0.10) 0%, transparent 45%),
            radial-gradient(ellipse at 50% 100%, rgba(0,60,120,0.18)  0%, transparent 60%),
            #080d14;
        min-height: 100vh;
    }
    [data-testid="stMain"]           { background: transparent; }
    [data-testid="stMainBlockContainer"] { padding-top: 0 !important; }

    /* ── Constrain max width so content doesn't sprawl on ultrawide ── */
    [data-testid="stMainBlockContainer"] > div {
        max-width: 1200px;
        margin: 0 auto;
    }

    /* ════════════════════════════════════════════
       HERO
    ════════════════════════════════════════════ */
    .hero {
        background:
            linear-gradient(135deg, #071428 0%, #0b2550 35%, #0a4a9e 68%, #0072C6 85%, #00AEEF 100%);
        border-radius: 0 0 28px 28px;
        padding: 2.4rem 3rem 1.8rem;
        margin-bottom: 2.2rem;
        box-shadow: 0 12px 60px rgba(0,114,198,0.40), inset 0 1px 0 rgba(255,255,255,0.07);
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -30%; right: -5%;
        width: 480px; height: 480px;
        background: radial-gradient(circle, rgba(0,174,239,0.20) 0%, transparent 65%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero::after {
        content: '';
        position: absolute;
        bottom: -20%; left: 20%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(0,80,180,0.15) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-inner {
        position: relative; z-index: 1;
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1.5rem;
        flex-wrap: wrap;
    }
    .hero-left h1 {
        color: #ffffff;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.025em;
        text-shadow: 0 2px 16px rgba(0,0,0,0.4);
    }
    .hero-left p {
        color: #a8d8f0;
        font-size: 0.93rem;
        margin: 0 0 0.9rem 0;
    }
    .hero .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(255,255,255,0.10);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.16);
        color: #dff3ff;
        border-radius: 999px;
        padding: 0.24rem 0.85rem;
        font-size: 0.74rem;
        font-weight: 600;
        margin-right: 0.35rem;
        letter-spacing: 0.03em;
    }
    .hero-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.55rem;
        min-width: 160px;
    }
    .hero-user {
        font-size: 0.76rem;
        color: rgba(255,255,255,0.55);
        text-align: right;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
    }

    /* ── Hero sign-out — native HTML button inside the hero markup ── */
    .hero-signout-btn {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.25);
        color: #dff3ff;
        font-family: inherit;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        padding: 0.42rem 1.2rem;
        border-radius: 999px;
        cursor: pointer;
        backdrop-filter: blur(8px);
        transition: background 0.18s;
        white-space: nowrap;
    }
    .hero-signout-btn:hover {
        background: rgba(255,255,255,0.20);
    }

    /* ── Hero stats bar ── */
    .hero-stats {
        position: relative; z-index: 1;
        display: flex;
        gap: 0;
        margin-top: 1.4rem;
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 1.2rem;
    }
    .hero-stat {
        flex: 1;
        padding: 0 1.4rem;
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    .hero-stat:first-child { padding-left: 0; }
    .hero-stat:last-child  { border-right: none; }
    .hero-stat-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255,255,255,0.45);
        margin-bottom: 0.2rem;
    }
    .hero-stat-val {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
    }

    /* ════════════════════════════════════════════
       FORM PANELS
    ════════════════════════════════════════════ */
    .form-panel {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 1.6rem 1.8rem 1.4rem;
        backdrop-filter: blur(14px);
        box-shadow: 0 4px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
        margin-bottom: 0.6rem;
    }
    .panel-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.73rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #00AEEF;
        margin: 0 0 1.2rem 0;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid rgba(0,174,239,0.18);
    }
    .panel-icon {
        width: 26px; height: 26px;
        background: rgba(0,174,239,0.15);
        border-radius: 7px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
    }

    /* ── Field labels ── */
    label { font-size: 0.81rem !important; color: #8b95a3 !important; font-weight: 500 !important; }

    /* ── Text / Number inputs ── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #f0f4f8 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 0.9rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #00AEEF !important;
        box-shadow: 0 0 0 3px rgba(0,174,239,0.18), 0 0 16px rgba(0,174,239,0.10) !important;
        outline: none !important;
    }
    [data-testid="stNumberInput"] button {
        background: rgba(255,255,255,0.06) !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: #9ca3af !important;
        border-radius: 8px !important;
    }

    /* ── Select / Multiselect ── */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stMultiSelect"] > div > div:first-child {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #f0f4f8 !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stSelectbox"] svg,
    [data-testid="stMultiSelect"] svg { color: #6b7280 !important; }

    /* Multiselect tags */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background: rgba(0,114,198,0.22) !important;
        border: 1px solid rgba(0,174,239,0.3) !important;
        border-radius: 6px !important;
        color: #a8d8f0 !important;
        font-size: 0.8rem !important;
    }

    /* Slider track */
    [data-testid="stSlider"] [role="slider"] {
        background: #00AEEF !important;
        border: 2px solid #00AEEF !important;
        box-shadow: 0 0 0 4px rgba(0,174,239,0.2) !important;
    }
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="progressbar"] {
        background: linear-gradient(90deg, #0072C6, #00AEEF) !important;
    }

    /* ── Evaluate / Login buttons ── */
    div.stButton > button {
        background: linear-gradient(90deg, #0057a8 0%, #0072C6 40%, #00AEEF 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.8rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        box-shadow: 0 4px 24px rgba(0,174,239,0.45), inset 0 1px 0 rgba(255,255,255,0.15) !important;
        transition: all 0.18s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        box-shadow: 0 6px 36px rgba(0,174,239,0.75), inset 0 1px 0 rgba(255,255,255,0.22) !important;
        transform: translateY(-2px) !important;
        filter: brightness(1.12) !important;
    }
    div.stButton > button:active {
        transform: translateY(0) !important;
        filter: none !important;
    }

    /* ── Login form card ── */
    [data-testid="stForm"] {
        background: rgba(8, 13, 24, 0.82) !important;
        border-radius: 22px !important;
        padding: 2.2rem 2rem 1.8rem !important;
        backdrop-filter: blur(32px) !important;
        box-shadow:
            0 0 0 1.5px rgba(0,174,239,0.5),
            0 12px 60px rgba(0,114,198,0.45),
            0 2px 80px rgba(0,174,239,0.12) !important;
        margin-top: 0.5rem !important;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #0057a8 0%, #00AEEF 100%) !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(0,174,239,0.5) !important;
        width: 100% !important;
    }

    /* ════════════════════════════════════════════
       SECTION TITLE
    ════════════════════════════════════════════ */
    .section-title {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        color: #00AEEF;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0,174,239,0.18);
    }

    /* ════════════════════════════════════════════
       METRIC CARDS
    ════════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 16px !important;
        padding: 1.15rem 1.25rem !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 28px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        transition: box-shadow 0.2s, transform 0.2s !important;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 6px 36px rgba(0,174,239,0.20), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.74rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.07em !important;
        text-transform: uppercase !important;
        color: #6b7280 !important;
    }

    /* ════════════════════════════════════════════
       VERDICT BANNERS
    ════════════════════════════════════════════ */
    .verdict-wrap {
        display: flex;
        align-items: center;
        gap: 1.4rem;
        border-radius: 18px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.6rem;
        position: relative;
        overflow: hidden;
    }
    .verdict-wrap::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 250px; height: 100%;
        background: radial-gradient(ellipse at right, rgba(255,255,255,0.06) 0%, transparent 70%);
    }
    .verdict-approve { background: linear-gradient(135deg, #052e1b 0%, #065f46 50%, #047857 100%); border: 1px solid rgba(16,185,129,0.35); box-shadow: 0 6px 32px rgba(16,185,129,0.18); }
    .verdict-escalate { background: linear-gradient(135deg, #3a1500 0%, #78350f 50%, #92400e 100%); border: 1px solid rgba(245,158,11,0.35); box-shadow: 0 6px 32px rgba(245,158,11,0.16); }
    .verdict-reject { background: linear-gradient(135deg, #3a0808 0%, #7f1d1d 50%, #991b1b 100%); border: 1px solid rgba(239,68,68,0.35); box-shadow: 0 6px 32px rgba(239,68,68,0.18); }
    .verdict-icon-big { font-size: 2.4rem; line-height: 1; flex-shrink: 0; }
    .verdict-body { flex: 1; }
    .verdict-label { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.5); margin-bottom: 0.15rem; }
    .verdict-text  { font-size: 1.45rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em; line-height: 1.15; }
    .verdict-sub   { font-size: 0.84rem; color: rgba(255,255,255,0.6); margin-top: 0.3rem; }
    .verdict-score {
        text-align: center;
        padding: 0.8rem 1.4rem;
        background: rgba(0,0,0,0.25);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(8px);
        flex-shrink: 0;
    }
    .verdict-score-num { font-size: 2.1rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em; line-height: 1; }
    .verdict-score-label { font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.45); margin-top: 0.2rem; }

    /* ════════════════════════════════════════════
       ANOMALY PILLS
    ════════════════════════════════════════════ */
    .pill {
        display: inline-block;
        background: rgba(239,68,68,0.12);
        color: #fca5a5;
        border: 1px solid rgba(239,68,68,0.25);
        border-radius: 999px;
        padding: 0.28rem 0.9rem;
        font-size: 0.79rem;
        font-weight: 500;
        margin: 0.2rem 0.22rem 0.2rem 0;
    }
    .pill-clean {
        display: inline-block;
        background: rgba(16,185,129,0.1);
        color: #6ee7b7;
        border: 1px solid rgba(16,185,129,0.22);
        border-radius: 999px;
        padding: 0.28rem 0.9rem;
        font-size: 0.79rem;
        font-weight: 500;
    }

    /* ════════════════════════════════════════════
       VISUAL TRACEABILITY
    ════════════════════════════════════════════ */
    .trace-claim-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    .trace-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 0.42rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.87rem;
    }
    .trace-row:last-child { border-bottom: none; }
    .trace-key { color: #6b7280; font-weight: 500; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .trace-val { font-weight: 600; text-align: right; max-width: 58%; word-break: break-word; }
    .trace-val.risk { color: #fca5a5; }
    .trace-val.warn { color: #fcd34d; }
    .trace-val.ok   { color: #6ee7b7; }

    .trace-policy-card {
        background: rgba(0,114,198,0.07);
        border: 1px solid rgba(0,174,239,0.18);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px rgba(0,114,198,0.12);
    }
    .clause-block {
        background: rgba(0,174,239,0.06);
        border: 1px solid rgba(0,174,239,0.14);
        border-left: 3px solid #00AEEF;
        border-radius: 0 10px 10px 0;
        padding: 0.75rem 1rem;
        margin-bottom: 0.7rem;
        color: #a8d8f0;
        font-size: 0.84rem;
        line-height: 1.65;
    }
    .clause-block:last-child { margin-bottom: 0; }
    .clause-num { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #00AEEF; margin-bottom: 0.28rem; }

    /* ── Connector ── */
    .connector-bar {
        display: flex; align-items: center; justify-content: center; gap: 0.6rem;
        padding: 1rem 0 0.5rem;
        color: #4b5563; font-size: 0.78rem; font-weight: 600;
        letter-spacing: 0.09em; text-transform: uppercase;
    }
    .connector-bar::before, .connector-bar::after {
        content: ''; flex: 1; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,174,239,0.25), transparent);
    }

    /* ── AI Decision Panel ── */
    .ai-decision-panel {
        background: rgba(0,174,239,0.04);
        border: 1px solid rgba(0,174,239,0.18);
        border-radius: 18px;
        padding: 1.5rem 1.8rem;
        backdrop-filter: blur(14px);
        box-shadow: 0 6px 36px rgba(0,114,198,0.14), inset 0 1px 0 rgba(0,174,239,0.1);
        margin-bottom: 1rem;
    }
    .ai-header { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.85rem; }
    .ai-badge {
        background: linear-gradient(90deg, rgba(0,114,198,0.35), rgba(0,174,239,0.22));
        border: 1px solid rgba(0,174,239,0.28);
        border-radius: 999px;
        padding: 0.18rem 0.72rem;
        font-size: 0.68rem; font-weight: 700; color: #00AEEF;
        letter-spacing: 0.1em; text-transform: uppercase;
    }
    .ai-title { font-size: 0.8rem; font-weight: 700; color: #9ca3af; letter-spacing: 0.06em; text-transform: uppercase; }
    .ai-body  { color: #cbd5e1; font-size: 0.92rem; line-height: 1.82; }

    /* ── Expander glass ── */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
    }

    /* ── Divider ── */
    hr { border: none; border-top: 1px solid rgba(255,255,255,0.06) !important; margin: 0.4rem 0 1.6rem; }

    /* ── Placeholder state ── */
    .placeholder-state {
        text-align: center;
        padding: 3rem 0 2.5rem;
        color: #4b5563;
    }
    .placeholder-state .ph-icon { font-size: 2.8rem; margin-bottom: 0.8rem; opacity: 0.6; }
    .placeholder-state p { font-size: 0.95rem; }
    .placeholder-state strong { color: #00AEEF; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def _is_authenticated() -> bool:
    return bool(st.session_state.get("access_token"))

def _store_session(session) -> None:
    st.session_state["access_token"] = session.access_token
    st.session_state["user_email"] = session.user.email

def _clear_session() -> None:
    for key in ("access_token", "user_email"):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Login screen
# ---------------------------------------------------------------------------
def show_login() -> None:
    st.markdown("""
    <div style="text-align:center;margin-top:3rem;margin-bottom:0.5rem">
        <div style="font-size:3.2rem;line-height:1;filter:drop-shadow(0 0 18px rgba(0,174,239,0.5))">🛡️</div>
        <div style="color:#ffffff;font-size:1.65rem;font-weight:800;
                    letter-spacing:-0.025em;margin-top:0.6rem;
                    text-shadow:0 2px 14px rgba(0,0,0,0.5)">
            Insurance AI Risk Underwriter
        </div>
        <div style="color:#4b5563;font-size:0.88rem;margin-top:0.45rem">
            Powered by IBM watsonx.ai · Supabase · FastAPI
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, card_col, _ = st.columns([1, 2, 1])
    with card_col:
        st.markdown(
            """<h2 style="
                text-align:center; margin:0.6rem 0 1.3rem 0;
                font-size:1.4rem; font-weight:800; letter-spacing:-0.02em;
                background:-webkit-linear-gradient(left, #0072C6, #00AEEF);
                -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                filter:drop-shadow(0 0 10px rgba(0,174,239,0.4));
            ">🔐 Underwriter Portal</h2>""",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            email    = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter both your email and password.")
                return
            try:
                resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
                _store_session(resp.session)
                st.rerun()
            except Exception as exc:
                msg = str(exc)
                if "Invalid login credentials" in msg or "invalid_credentials" in msg:
                    st.error("❌ Incorrect email or password.")
                elif "Email not confirmed" in msg:
                    st.error("📧 Please confirm your email before signing in.")
                else:
                    st.error(f"❌ Sign-in failed: {msg}")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]

def _code_only(opt: str) -> str:
    """Extract bare code from 'I21.9 — Description' display option."""
    return opt.split("—")[0].strip()


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------
def show_dashboard() -> None:

    user_email = st.session_state.get("user_email", "")

    # ── Hero — fully self-contained, sign-out button lives inside the banner ──
    st.markdown(f"""
    <div class="hero">
        <div class="hero-inner">
            <div class="hero-left">
                <h1>🛡️ Insurance AI Risk Underwriter</h1>
                <p>Enterprise-grade actuarial claim evaluation powered by IBM watsonx.ai</p>
                <div>
                    <span class="badge">⚡ IBM watsonx</span>
                    <span class="badge">🤖 Mistral Large</span>
                    <span class="badge">🗄️ Supabase pgvector</span>
                    <span class="badge">🔒 ES256 JWT</span>
                </div>
            </div>
            <div class="hero-right">
                <div class="hero-user">{user_email}</div>
                <button class="hero-signout-btn"
                        onclick="window.location.href='?signout=1'">
                    Sign Out
                </button>
            </div>
        </div>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-label">AI Engine</div>
                <div class="hero-stat-val">Mistral Large 25.12</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-label">Embeddings</div>
                <div class="hero-stat-val">Slate 30M · 384-dim</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-label">Vector Store</div>
                <div class="hero-stat-val">Supabase pgvector</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-label">Auth</div>
                <div class="hero-stat-val">ES256 · Zero-latency</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sign-out via query param — no visible Streamlit button needed
    if st.query_params.get("signout") == "1":
        st.query_params.clear()
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        _clear_session()
        st.rerun()

    # ── Two-column form ──────────────────────────────────────────────────────
    form_left, form_right = st.columns(2, gap="large")

    with form_left:
        st.markdown(
            '<div class="form-panel">'
            '<div class="panel-title"><span class="panel-icon">📋</span> Claim Submission</div>',
            unsafe_allow_html=True,
        )

        claim_id              = st.text_input("Claim ID", value="CLM-001", placeholder="CLM-001")
        claim_policy_id       = st.text_input("Policy ID", value="POL-777", placeholder="POL-777", key="cpid")

        claim_amount = st.number_input(
            "Claim Amount ($)",
            min_value=0.0, value=150000.0, step=1000.0, format="%.2f",
        )

        months_since_inception = st.select_slider(
            "Months Since Policy Inception",
            options=list(range(0, 361)),
            value=5,
            help="Drag to set the number of months since the policy started",
        )

        # ICD-10 multiselect with freetext fallback
        diag_selected = st.multiselect(
            "Diagnosis Codes",
            options=ICD10_OPTIONS,
            default=["I21.9 — Acute Myocardial Infarction"],
            help="Select one or more ICD-10 codes. Add custom codes in the field below.",
        )
        diag_extra = st.text_input(
            "Additional / Custom Codes (comma-separated)",
            value="",
            placeholder="e.g. Z87.39, M54.5",
            key="diag_extra",
        )

        st.markdown('</div>', unsafe_allow_html=True)

    with form_right:
        st.markdown(
            '<div class="form-panel">'
            '<div class="panel-title"><span class="panel-icon">👤</span> Policyholder Profile</div>',
            unsafe_allow_html=True,
        )

        profile_policy_id = st.text_input(
            "Policy ID", value="POL-777", placeholder="POL-777", key="ppid",
            help="Must match the Policy ID in the Claim Submission",
        )

        age = st.select_slider(
            "Claimant Age",
            options=list(range(18, 111)),
            value=45,
            help="Slide to set claimant age. Age > 65 activates the High-Risk Triangle check.",
        )

        annual_income = st.number_input(
            "Annual Income ($)",
            min_value=0.0, value=25000.0, step=500.0, format="%.2f",
        )

        # Medical history multiselect
        history_selected = st.multiselect(
            "Medical History Flags",
            options=MEDICAL_FLAG_OPTIONS,
            default=["Hypertension"],
            help="Select all conditions declared at application time.",
        )
        history_extra = st.text_input(
            "Additional History (comma-separated)",
            value="",
            placeholder="e.g. Rare genetic condition, Prior surgery",
            key="hist_extra",
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # Live claim/income ratio hint
    income_ratio_live = claim_amount / annual_income if annual_income > 0 else 0
    ratio_color = "#fca5a5" if income_ratio_live > 5 else ("#fcd34d" if income_ratio_live > 3 else "#6ee7b7")
    ratio_label = "⚠️ Anti-selection risk" if income_ratio_live > 5 else ("⚡ Elevated" if income_ratio_live > 3 else "✓ Within range")
    st.markdown(
        f'<div style="text-align:center;font-size:0.82rem;color:{ratio_color};'
        f'margin:-0.4rem 0 1rem;font-weight:600">'
        f'Live Claim / Income Ratio: {income_ratio_live:.1f}× — {ratio_label}</div>',
        unsafe_allow_html=True,
    )

    # ── Evaluate button ──────────────────────────────────────────────────────
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        evaluate_btn = st.button("⚡  Evaluate Risk Now", use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Pre-evaluation placeholder ───────────────────────────────────────────
    if not evaluate_btn:
        st.markdown(
            '<div class="placeholder-state">'
            '<div class="ph-icon">📊</div>'
            '<p>Fill in the claim and profile above, then click '
            '<strong>Evaluate Risk Now</strong> to run the AI analysis.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Build payload — merge multiselect + freetext ────────────────────────
    diagnosis_codes_raw = ", ".join(
        [_code_only(d) for d in diag_selected] + parse_list(diag_extra)
    )
    medical_history_raw = ", ".join(
        [h.lower() for h in history_selected] + parse_list(history_extra)
    )

    payload = {
        "claim": {
            "claim_id":               claim_id.strip(),
            "policy_id":              claim_policy_id.strip(),
            "claim_amount":           float(claim_amount),
            "months_since_inception": int(months_since_inception),
            "diagnosis_codes":        parse_list(diagnosis_codes_raw),
        },
        "profile": {
            "policy_id":             profile_policy_id.strip(),
            "age":                   int(age),
            "annual_income":         float(annual_income),
            "medical_history_flags": parse_list(medical_history_raw),
        },
    }

    access_token = st.session_state["access_token"]

    with st.spinner("🤖 Sending to IBM watsonx AI — retrieving policy clauses and evaluating claim…"):
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/evaluate-claim",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=90,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to the backend. Is the FastAPI server running on port 8000?")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out after 90 seconds.")
            st.stop()
        except requests.exceptions.HTTPError:
            if response.status_code == 401:
                st.error("🔒 Session expired. Please sign in again.")
                _clear_session()
                st.rerun()
            detail = ""
            try:
                detail = response.json().get("detail", "")
            except Exception:
                pass
            st.error(f"❌ API error {response.status_code}: {detail or response.text}")
            st.stop()

    # ── Unpack ───────────────────────────────────────────────────────────────
    risk_score:       float = result["risk_score"]
    recommendation:   str   = result["recommendation"]
    ai_reasoning:     str   = result["ai_reasoning"]
    flagged_anomalies: list = result.get("flagged_anomalies", [])
    policy_clauses_raw: str = result.get("policy_clauses") or ""
    rec_lower = recommendation.lower()

    # ── Results heading ───────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.72rem;font-weight:800;letter-spacing:0.13em;'
        'text-transform:uppercase;color:#4b5563;margin-bottom:1rem">📊 Evaluation Results</div>',
        unsafe_allow_html=True,
    )

    # ── Verdict banner ────────────────────────────────────────────────────────
    score_pct = int(risk_score * 100)
    if "approve" in rec_lower:
        verdict_cls  = "verdict-approve"
        verdict_icon = "✅"
        verdict_sub  = "Claim cleared for processing — no significant risk flags detected."
    elif "escalate" in rec_lower:
        verdict_cls  = "verdict-escalate"
        verdict_icon = "⚠️"
        verdict_sub  = "Manual underwriter review required before this claim can proceed."
    else:
        verdict_cls  = "verdict-reject"
        verdict_icon = "🚫"
        verdict_sub  = "Claim does not meet approval criteria — refer to flagged anomalies below."

    st.markdown(f"""
    <div class="verdict-wrap {verdict_cls}">
        <div class="verdict-icon-big">{verdict_icon}</div>
        <div class="verdict-body">
            <div class="verdict-label">AI Verdict</div>
            <div class="verdict-text">{recommendation}</div>
            <div class="verdict-sub">{verdict_sub}</div>
        </div>
        <div class="verdict-score">
            <div class="verdict-score-num">{score_pct}%</div>
            <div class="verdict-score-label">Risk Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key metrics row ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    if risk_score < 0.4:
        score_delta, delta_color = "Low risk", "normal"
    elif risk_score < 0.7:
        score_delta, delta_color = "Medium risk", "off"
    else:
        score_delta, delta_color = "High risk", "inverse"

    with m1:
        st.metric("🎯 Risk Score", f"{risk_score:.2f}", score_delta, delta_color=delta_color)
    with m2:
        st.metric(
            "🚩 Anomalies",
            str(len(flagged_anomalies)),
            "flags detected" if flagged_anomalies else "all clear",
            delta_color="inverse" if flagged_anomalies else "normal",
        )
    with m3:
        st.metric(
            "📅 Policy Age",
            f"{months_since_inception} mo.",
            "Early claim ⚠️" if months_since_inception < 12 else "Normal tenure",
            delta_color="inverse" if months_since_inception < 12 else "normal",
        )
    with m4:
        income_ratio = claim_amount / annual_income if annual_income > 0 else 0
        st.metric(
            "💰 Claim / Income",
            f"{income_ratio:.1f}×",
            "Anti-selection risk" if income_ratio > 5 else "Within range",
            delta_color="inverse" if income_ratio > 5 else "normal",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Visual Traceability ───────────────────────────────────────────────────
    st.markdown('<div class="section-title">🔬 Visual Traceability</div>', unsafe_allow_html=True)

    trace_left, trace_right = st.columns(2, gap="large")

    with trace_left:
        ratio_cls  = "risk" if income_ratio > 5 else ("warn" if income_ratio > 3 else "ok")
        tenure_cls = "risk" if months_since_inception < 12 else ("warn" if months_since_inception < 36 else "ok")
        age_cls    = "warn" if age > 65 else "ok"
        diag_disp  = parse_list(diagnosis_codes_raw)
        hist_disp  = parse_list(medical_history_raw)

        rows = [
            ("Claim ID",       claim_id,                           "ok"),
            ("Policy ID",      claim_policy_id,                    "ok"),
            ("Age",            f"{age} yrs",                       age_cls),
            ("Claim Amount",   f"${claim_amount:,.2f}",            ratio_cls),
            ("Annual Income",  f"${annual_income:,.2f}",           "ok"),
            ("Claim / Income", f"{income_ratio:.1f}×",             ratio_cls),
            ("Policy Tenure",  f"{months_since_inception} months", tenure_cls),
            ("Diagnosis",      ", ".join(diag_disp) or "None",     "warn" if diag_disp else "ok"),
            ("Med. History",   ", ".join(hist_disp) or "None",     "ok"),
        ]

        rows_html = "".join(
            f'<div class="trace-row">'
            f'<span class="trace-key">{lbl}</span>'
            f'<span class="trace-val {cls}">{val}</span>'
            f'</div>'
            for lbl, val, cls in rows
        )
        st.markdown(
            f'<div class="trace-claim-card">{rows_html}</div>',
            unsafe_allow_html=True,
        )

    with trace_right:
        raw_clauses = [c.strip() for c in policy_clauses_raw.split("\n\n") if c.strip()]
        if raw_clauses:
            clauses_html = ""
            for i, clause in enumerate(raw_clauses, 1):
                safe = clause.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                clauses_html += (
                    f'<div class="clause-block">'
                    f'<div class="clause-num">Retrieved Clause {i}</div>'
                    f'{safe}</div>'
                )
            st.markdown(f'<div class="trace-policy-card">{clauses_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="trace-policy-card"><div class="clause-block">'
                '<div class="clause-num">No Clauses Retrieved</div>'
                'No matching policy rules found in the vector store. '
                'Ingest documents via <code>/api/v1/ingest-documents</code> to enable clause citation.'
                '</div></div>',
                unsafe_allow_html=True,
            )

    # ── Anomaly pills ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🚩 Flagged Anomalies</div>', unsafe_allow_html=True)
    if flagged_anomalies:
        pills = " ".join(f'<span class="pill">{a}</span>' for a in flagged_anomalies)
        st.markdown(f'<div style="margin-top:0.35rem">{pills}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill-clean">✓ No anomalies detected</span>', unsafe_allow_html=True)

    # ── Connector ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="connector-bar">🤖 Mistral Large connected the dots</div>',
        unsafe_allow_html=True,
    )

    # ── AI Decision panel ──────────────────────────────────────────────────────
    st.markdown(
        f'<div class="ai-decision-panel">'
        f'<div class="ai-header">'
        f'<span class="ai-badge">IBM watsonx · Mistral Large</span>'
        f'<span class="ai-title">AI Decision Reasoning</span>'
        f'</div>'
        f'<div class="ai-body">{ai_reasoning}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Raw JSON ───────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔍 Raw API Response"):
        st.json(result)


# ---------------------------------------------------------------------------
# Entry point — auth gate
# ---------------------------------------------------------------------------
if _is_authenticated():
    show_dashboard()
else:
    show_login()
