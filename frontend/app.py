"""
Trace: Enterprise AI Underwriter – Streamlit frontend
Backend URL is configured via the BACKEND_URL environment variable or st.secrets.
Defaults to the Render deployment; override with http://localhost:8000 for local dev.
"""

import os
import streamlit as st
import requests
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Page config  ── must be FIRST Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Trace: Enterprise AI Underwriter",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Secrets helper  (env → st.secrets fallback)
# ---------------------------------------------------------------------------
def _get_secret(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        try:
            value = st.secrets[key]
        except (KeyError, FileNotFoundError):
            value = ""
    return value or ""

# ---------------------------------------------------------------------------
# Backend URL  ── set BACKEND_URL in your env / Streamlit Cloud secrets to
# override.  Falls back to the Render deployment so Cloud hosting works OOTB.
# For local dev: BACKEND_URL=http://localhost:8000
# ---------------------------------------------------------------------------
_BACKEND_URL = (
    _get_secret("BACKEND_URL") or "https://trace-api-u4rx.onrender.com"
).rstrip("/")

# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------

_SUPABASE_URL = _get_secret("SUPABASE_URL")
_SUPABASE_KEY = _get_secret("SUPABASE_KEY")

@st.cache_resource
def _get_supabase_client() -> Client | None:
    if not _SUPABASE_URL or not _SUPABASE_KEY:
        return None
    return create_client(_SUPABASE_URL.rstrip("/"), _SUPABASE_KEY.strip())

supabase: Client | None = _get_supabase_client()
if supabase is None:
    st.error(
        "⚠️ **Supabase credentials are not configured.**\n\n"
        "Add `SUPABASE_URL` and `SUPABASE_KEY` to your Streamlit Cloud secrets "
        "(**App settings → Secrets**).",
        icon="🔐",
    )
    st.stop()

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
        background: #0a0f1e;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        padding: 1.6rem 2.8rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    /* Subtle left-edge accent bar */
    .hero::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
        background: linear-gradient(180deg, #0072C6 0%, #00AEEF 100%);
    }
    /* Faint deep-blue glow, bottom-right — almost invisible, just adds depth */
    .hero::after {
        content: '';
        position: absolute;
        bottom: -60%; right: -8%;
        width: 420px; height: 420px;
        background: radial-gradient(circle, rgba(0,114,198,0.10) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-inner {
        position: relative; z-index: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
    }
    .hero-left {
        display: flex;
        align-items: center;
        gap: 1.2rem;
    }
    .hero-logo {
        width: 44px; height: 44px;
        background: linear-gradient(135deg, #0057a8, #00AEEF);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem;
        flex-shrink: 0;
        box-shadow: 0 4px 16px rgba(0,114,198,0.4);
    }
    .hero-title-group h1 {
        color: #f1f5f9;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .hero-title-group p {
        color: #475569;
        font-size: 0.8rem;
        margin: 0.18rem 0 0;
        font-weight: 400;
        letter-spacing: 0.01em;
    }
    .hero-right {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .hero-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(16,185,129,0.08);
        border: 1px solid rgba(16,185,129,0.2);
        border-radius: 999px;
        padding: 0.32rem 0.9rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #6ee7b7;
        letter-spacing: 0.03em;
    }
    .hero-status-dot {
        width: 6px; height: 6px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 6px rgba(16,185,129,0.7);
        animation: pulse-dot 2s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0.4; }
    }

    /* ── Hero sign-out button ── */
    .hero-signout-btn {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.12);
        color: #64748b;
        font-family: inherit;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.04em;
        padding: 0.38rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        transition: border-color 0.15s, color 0.15s;
        white-space: nowrap;
    }
    .hero-signout-btn:hover {
        border-color: rgba(239,68,68,0.4);
        color: #fca5a5;
    }

    /* ════════════════════════════════════════════
       MOBILE RESPONSIVE — hero + layout
    ════════════════════════════════════════════ */
    @media (max-width: 640px) {
        .hero {
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
        }
        .hero-inner {
            flex-wrap: wrap;
            gap: 0.75rem;
        }
        .hero-left {
            gap: 0.75rem;
            flex: 1 1 auto;
            min-width: 0;
        }
        .hero-logo {
            width: 36px; height: 36px;
            font-size: 1.1rem;
            flex-shrink: 0;
        }
        .hero-title-group h1 {
            font-size: 0.95rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .hero-title-group p {
            display: none;
        }
        .hero-right {
            gap: 0.5rem;
            flex-shrink: 0;
        }
        .hero-status-pill {
            font-size: 0.65rem;
            padding: 0.25rem 0.6rem;
        }
        .hero-signout-btn {
            font-size: 0.68rem;
            padding: 0.3rem 0.65rem;
        }
        .form-panel {
            padding: 1.1rem 1rem 1rem;
            border-radius: 12px;
        }
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
       VERDICT CARD  — redesigned
    ════════════════════════════════════════════ */
    .verdict-card {
        display: flex;
        align-items: stretch;
        gap: 0;
        background: #0d1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        margin-bottom: 1.6rem;
        overflow: hidden;
        box-shadow: 0 8px 40px rgba(0,0,0,0.45);
        position: relative;
    }

    /* Left coloured accent bar */
    .verdict-accent {
        width: 5px;
        flex-shrink: 0;
        border-radius: 16px 0 0 16px;
    }
    .verdict-approve  .verdict-accent { background: linear-gradient(180deg, #059669, #10b981); }
    .verdict-escalate .verdict-accent { background: linear-gradient(180deg, #d97706, #f59e0b); }
    .verdict-reject   .verdict-accent { background: linear-gradient(180deg, #dc2626, #ef4444); }

    /* Main content area */
    .verdict-content {
        flex: 1;
        padding: 1.5rem 1.8rem;
        display: flex;
        align-items: center;
        gap: 1.6rem;
    }

    /* Status chip */
    .verdict-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border-radius: 6px;
        padding: 0.22rem 0.75rem;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
        width: fit-content;
    }
    .verdict-approve  .verdict-chip { background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); color: #6ee7b7; }
    .verdict-escalate .verdict-chip { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.3); color: #fcd34d; }
    .verdict-reject   .verdict-chip { background: rgba(239,68,68,0.12);  border: 1px solid rgba(239,68,68,0.3);  color: #fca5a5; }
    .verdict-chip-dot {
        width: 5px; height: 5px;
        border-radius: 50%;
    }
    .verdict-approve  .verdict-chip-dot { background: #10b981; }
    .verdict-escalate .verdict-chip-dot { background: #f59e0b; }
    .verdict-reject   .verdict-chip-dot { background: #ef4444; }

    .verdict-body     { flex: 1; }
    .verdict-decision { font-size: 1.35rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.02em; line-height: 1.2; margin-bottom: 0.3rem; }
    .verdict-sub      { font-size: 0.83rem; color: #475569; line-height: 1.55; }

    /* Divider between body and score */
    .verdict-divider {
        width: 1px;
        background: rgba(255,255,255,0.07);
        margin: 1.2rem 0;
        flex-shrink: 0;
    }

    /* Score ring section */
    .verdict-score-section {
        padding: 1.5rem 2rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        flex-shrink: 0;
    }
    .verdict-ring-wrap {
        position: relative;
        width: 72px; height: 72px;
    }
    .verdict-ring-wrap svg {
        transform: rotate(-90deg);
    }
    .verdict-ring-bg {
        fill: none;
        stroke: rgba(255,255,255,0.07);
        stroke-width: 5;
    }
    .verdict-ring-fill {
        fill: none;
        stroke-width: 5;
        stroke-linecap: round;
        transition: stroke-dashoffset 0.6s ease;
    }
    .verdict-approve  .verdict-ring-fill { stroke: #10b981; }
    .verdict-escalate .verdict-ring-fill { stroke: #f59e0b; }
    .verdict-reject   .verdict-ring-fill { stroke: #ef4444; }
    .verdict-ring-label {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        font-size: 1.05rem;
        font-weight: 800;
        color: #f1f5f9;
        letter-spacing: -0.02em;
        line-height: 1;
    }
    .verdict-score-caption {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #374151;
        text-align: center;
    }

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

    /* ════════════════════════════════════════════
       AUDIT GUARDRAIL BANNER
    ════════════════════════════════════════════ */
    .audit-banner {
        display: flex;
        align-items: flex-start;
        gap: 1.2rem;
        background: #1a0e00;
        border: 1px solid rgba(251,191,36,0.35);
        border-left: 4px solid #f59e0b;
        border-radius: 14px;
        padding: 1.35rem 1.6rem;
        margin-bottom: 1.6rem;
        box-shadow: 0 4px 28px rgba(245,158,11,0.12);
    }
    .audit-banner-icon {
        font-size: 1.5rem;
        line-height: 1;
        flex-shrink: 0;
        margin-top: 0.05rem;
    }
    .audit-banner-body { flex: 1; }
    .audit-banner-title {
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #fcd34d;
        margin-bottom: 0.3rem;
    }
    .audit-banner-msg {
        font-size: 0.88rem;
        color: #92400e;
        color: #d97706;
        line-height: 1.65;
        margin-bottom: 0.45rem;
    }
    .audit-banner-reason {
        font-size: 0.8rem;
        color: #78350f;
        color: #92400e;
        font-style: italic;
        line-height: 1.55;
        border-top: 1px solid rgba(245,158,11,0.15);
        padding-top: 0.45rem;
        margin-top: 0.1rem;
    }

    /* ── PDF download button — override the default stDownloadButton ── */
    [data-testid="stDownloadButton"] > button {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        color: #94a3b8 !important;
        border-radius: 10px !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: none !important;
        transition: border-color 0.15s, color 0.15s, background 0.15s !important;
        width: 100% !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: rgba(0,174,239,0.08) !important;
        border-color: rgba(0,174,239,0.35) !important;
        color: #e2e8f0 !important;
        transform: none !important;
        filter: none !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session-state helpers
# Session is stored in st.session_state (in-memory) +
# Streamlit's own query-param token store for persistence across reruns.
# localStorage bridge removed — st.markdown <script> injection is unreliable
# in Streamlit Cloud's React/WebSocket architecture.
# ---------------------------------------------------------------------------

def _is_authenticated() -> bool:
    """Return True if a valid access token is present in session_state."""
    return bool(st.session_state.get("access_token"))

def _store_session(session) -> None:
    """Persist session into session_state after successful sign-in."""
    st.session_state["access_token"] = session.access_token
    st.session_state["user_email"]   = session.user.email

def _clear_session() -> None:
    """Wipe session_state — the next rerun will show the login screen."""
    for key in ("access_token", "user_email"):
        st.session_state.pop(key, None)

def _persist_to_local_storage(token: str, email: str) -> None:
    """No-op kept for call-site compatibility — localStorage bridge removed."""
    pass


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
            Trace: Enterprise AI Underwriter
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

        # ── Divider + ghost CTA ─────────────────────────────────────────────
        st.markdown("""
        <div style="
            display:flex; align-items:center; gap:0.75rem;
            margin: 0.9rem 0 0.75rem 0;
        ">
            <div style="flex:1; height:1px; background:rgba(255,255,255,0.08)"></div>
            <span style="color:#4b5563; font-size:0.72rem; letter-spacing:0.08em;
                         text-transform:uppercase; white-space:nowrap">
                Don't have access?
            </span>
            <div style="flex:1; height:1px; background:rgba(255,255,255,0.08)"></div>
        </div>
        <style>
            /* Ghost/outline style scoped to the request-access button only */
            div[data-testid="stVerticalBlock"] div.request-access-btn > div.stButton > button {
                background: transparent !important;
                color: #7ab3d4 !important;
                border: 1.5px solid rgba(122,179,212,0.4) !important;
                border-radius: 10px !important;
                font-size: 0.85rem !important;
                font-weight: 500 !important;
                letter-spacing: 0.06em !important;
                box-shadow: none !important;
                padding: 0.6rem 1.5rem !important;
                opacity: 0.85;
                transition: all 0.18s ease !important;
            }
            div[data-testid="stVerticalBlock"] div.request-access-btn > div.stButton > button:hover {
                background: rgba(122,179,212,0.07) !important;
                border-color: rgba(122,179,212,0.75) !important;
                color: #aed4ee !important;
                opacity: 1;
                transform: none !important;
                filter: none !important;
                box-shadow: none !important;
            }
        </style>
        """, unsafe_allow_html=True)

        # ── Access-request toggle + inline form ────────────────────────────
        if "show_access_form" not in st.session_state:
            st.session_state["show_access_form"] = False

        with st.container():
            st.markdown('<div class="request-access-btn">', unsafe_allow_html=True)
            if st.button(
                "Request Enterprise Access",
                use_container_width=True,
                help="Submit an access request to your IT administrator",
            ):
                st.session_state["show_access_form"] = not st.session_state["show_access_form"]
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state["show_access_form"]:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("access_request_form", clear_on_submit=True):
                st.markdown(
                    '<div style="font-size:0.8rem;font-weight:700;color:#7ab3d4;'
                    'letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.5rem">'
                    'Enterprise Access Request</div>',
                    unsafe_allow_html=True,
                )
                req_name  = st.text_input("Full Name",   placeholder="Jane Smith")
                req_email = st.text_input("Work Email",  placeholder="jane@company.com")
                req_role  = st.selectbox(
                    "Role",
                    ["Underwriter", "Actuary", "Compliance Officer", "IT Administrator", "Other"],
                )
                col_submit, col_cancel = st.columns([2, 1])
                with col_submit:
                    req_submitted = st.form_submit_button("Submit Request", use_container_width=True)
                with col_cancel:
                    req_cancelled = st.form_submit_button(
                        "Cancel",
                        use_container_width=True,
                        type="secondary",
                    )

            if req_cancelled:
                st.session_state["show_access_form"] = False
                st.rerun()

            if req_submitted:
                if not req_name.strip() or not req_email.strip():
                    st.error("Please fill in your name and work email.")
                else:
                    try:
                        ar = requests.post(
                            f"{_BACKEND_URL}/api/v1/access-request",
                            json={"name": req_name.strip(), "work_email": req_email.strip(), "role": req_role},
                            timeout=15,
                        )
                        if ar.status_code == 200:
                            st.session_state["show_access_form"] = False
                            st.toast("Access request submitted — IT admin will be in touch", icon="✅")
                            st.rerun()
                        else:
                            detail = ar.json().get("detail", ar.text)
                            st.error(f"❌ Submission failed: {detail}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Could not reach the backend: {e}")

        if submitted:
            if not email or not password:
                st.error("Please enter both your email and password.")
                return
            try:
                resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
                _store_session(resp.session)
                # Persist into localStorage so a browser refresh restores the session
                _persist_to_local_storage(
                    resp.session.access_token,
                    resp.session.user.email or "",
                )
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
# Helpers
# ---------------------------------------------------------------------------
def parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]

def _code_only(opt: str) -> str:
    """Extract bare code from 'I21.9 — Description' display option."""
    return opt.split("—")[0].strip()


def _build_audit_pdf(
    claim_id: str,
    policy_id: str,
    age: int,
    annual_income: float,
    claim_amount: float,
    months_since_inception: int,
    diagnosis_codes: list[str],
    medical_history: list[str],
    risk_score: float,
    recommendation: str,
    flagged_anomalies: list[str],
    ai_reasoning: str,
    policy_clauses_raw: str,
    requires_manual_audit: bool,
    audit_reason: str | None,
) -> bytes:
    """Build an in-memory PDF audit report and return the raw bytes.

    Uses reportlab.platypus for structured, paginated output.
    No files are written to disk — the document is built entirely in a
    BytesIO buffer and returned as bytes for Streamlit's download_button.
    """
    import io
    from datetime import datetime, timezone
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title=f"Underwriting Audit Report — {claim_id}",
        author="Trace: Enterprise AI Underwriter",
    )

    # ── Colour palette ───────────────────────────────────────────────────────
    C_NAVY       = colors.HexColor("#0a0f1e")
    C_BLUE       = colors.HexColor("#0072C6")
    C_CYAN       = colors.HexColor("#00AEEF")
    C_WHITE      = colors.white
    C_LIGHT_GREY = colors.HexColor("#f1f5f9")
    C_MID_GREY   = colors.HexColor("#94a3b8")
    C_DARK_GREY  = colors.HexColor("#334155")
    C_GREEN      = colors.HexColor("#059669")
    C_AMBER      = colors.HexColor("#d97706")
    C_RED        = colors.HexColor("#dc2626")
    C_RULE_LINE  = colors.HexColor("#1e293b")

    rec_lower = recommendation.lower()
    verdict_colour = (
        C_GREEN if "approve"  in rec_lower else
        C_AMBER if "escalate" in rec_lower else
        C_RED
    )

    # ── Paragraph styles ─────────────────────────────────────────────────────
    base    = getSampleStyleSheet()
    normal  = base["Normal"]

    def _style(name, **kwargs) -> ParagraphStyle:
        return ParagraphStyle(name, parent=normal, **kwargs)

    s_doc_title  = _style("DocTitle",   fontSize=18, fontName="Helvetica-Bold",   textColor=C_NAVY,       spaceAfter=2)
    s_doc_sub    = _style("DocSub",     fontSize=9,  fontName="Helvetica",        textColor=C_MID_GREY,   spaceAfter=14)
    s_section    = _style("Section",    fontSize=8,  fontName="Helvetica-Bold",   textColor=C_BLUE,       spaceBefore=14, spaceAfter=6, leading=10)
    s_field_key  = _style("FieldKey",   fontSize=8,  fontName="Helvetica-Bold",   textColor=C_DARK_GREY)
    s_field_val  = _style("FieldVal",   fontSize=9,  fontName="Helvetica",        textColor=C_NAVY)
    s_body       = _style("Body",       fontSize=9,  fontName="Helvetica",        textColor=C_DARK_GREY,  leading=14, spaceAfter=4)
    s_clause_hdr = _style("ClauseHdr",  fontSize=7,  fontName="Helvetica-Bold",   textColor=C_CYAN,       spaceAfter=2)
    s_clause     = _style("Clause",     fontSize=8,  fontName="Helvetica",        textColor=C_DARK_GREY,  leading=13)
    s_verdict    = _style("Verdict",    fontSize=13, fontName="Helvetica-Bold",   textColor=verdict_colour, spaceBefore=4, spaceAfter=2)
    s_anomaly    = _style("Anomaly",    fontSize=8,  fontName="Helvetica",        textColor=C_RED,        leftIndent=10, spaceAfter=2)
    s_footer     = _style("Footer",     fontSize=7,  fontName="Helvetica",        textColor=C_MID_GREY)
    s_audit_warn = _style("AuditWarn",  fontSize=8,  fontName="Helvetica-Bold",   textColor=C_AMBER,      spaceBefore=4, spaceAfter=2)
    s_audit_body = _style("AuditBody",  fontSize=8,  fontName="Helvetica-Oblique",textColor=C_AMBER,      leading=12, spaceAfter=4)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    income_ratio = claim_amount / annual_income if annual_income > 0 else 0

    # ── Build flowable story ──────────────────────────────────────────────────
    story = []

    # Header block
    story.append(Paragraph("Underwriting Audit Report", s_doc_title))
    story.append(Paragraph(f"Claim {claim_id} &nbsp;·&nbsp; Policy {policy_id} &nbsp;·&nbsp; Generated {generated_at}", s_doc_sub))
    story.append(HRFlowable(width="100%", thickness=1, color=C_RULE_LINE, spaceAfter=12))

    # ── Manual audit warning (shown only when guardrail fires) ──────────────
    if requires_manual_audit:
        audit_table_data = [[
            Paragraph("⚠  LOW CONFIDENCE — MANUAL AUDIT REQUIRED", s_audit_warn),
        ], [
            Paragraph(
                audit_reason or "The RAG policy context did not meet confidence thresholds. "
                "This AI-generated decision must not be actioned without human review.",
                s_audit_body,
            ),
        ]]
        audit_table = Table(audit_table_data, colWidths=["100%"])
        audit_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#1a0e00")),
            ("BOX",          (0, 0), (-1, -1), 1, colors.HexColor("#d97706")),
            ("LEFTPADDING",  (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", (0, 0), (-1, -1), 6),
        ]))
        story.append(KeepTogether([audit_table, Spacer(1, 0.3 * cm)]))

    # ── Section 1: Claim Details ─────────────────────────────────────────────
    story.append(Paragraph("SECTION 1 — CLAIM DETAILS", s_section))
    claim_table_data = [
        [Paragraph("Claim ID",                    s_field_key), Paragraph(claim_id,                         s_field_val),
         Paragraph("Policy ID",                   s_field_key), Paragraph(policy_id,                        s_field_val)],
        [Paragraph("Claim Amount",                s_field_key), Paragraph(f"${claim_amount:,.2f}",           s_field_val),
         Paragraph("Annual Income",               s_field_key), Paragraph(f"${annual_income:,.2f}",          s_field_val)],
        [Paragraph("Claim / Income Ratio",        s_field_key), Paragraph(f"{income_ratio:.1f}×",            s_field_val),
         Paragraph("Policy Tenure",               s_field_key), Paragraph(f"{months_since_inception} months",s_field_val)],
        [Paragraph("Claimant Age",                s_field_key), Paragraph(f"{age} yrs",                     s_field_val),
         Paragraph("Diagnosis Codes",             s_field_key), Paragraph(", ".join(diagnosis_codes) or "None", s_field_val)],
        [Paragraph("Medical History",             s_field_key), Paragraph(", ".join(medical_history) or "None", s_field_val),
         Paragraph("",                            s_field_key), Paragraph("",                                s_field_val)],
    ]
    col_w = doc.width / 4
    claim_table = Table(claim_table_data, colWidths=[col_w * 0.9, col_w * 1.1, col_w * 0.9, col_w * 1.1])
    claim_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), C_LIGHT_GREY),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS",(0, 0),(-1,-1), [C_LIGHT_GREY, colors.HexColor("#e8f4fd")]),
    ]))
    story.append(claim_table)

    # ── Section 2: AI Verdict ────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("SECTION 2 — AI VERDICT", s_section))

    score_pct = int(risk_score * 100)
    verdict_data = [
        [Paragraph("Recommendation", s_field_key), Paragraph(recommendation,      s_verdict)],
        [Paragraph("Risk Score",      s_field_key), Paragraph(f"{risk_score:.2f} ({score_pct}%)", s_field_val)],
    ]
    verdict_table = Table(verdict_data, colWidths=[doc.width * 0.3, doc.width * 0.7])
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), C_LIGHT_GREY),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(verdict_table)

    # Flagged anomalies
    if flagged_anomalies:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("Flagged Anomalies:", s_field_key))
        for anomaly in flagged_anomalies:
            story.append(Paragraph(f"• {anomaly}", s_anomaly))

    # ── Section 3: Retrieved Policy Clauses ──────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("SECTION 3 — RETRIEVED POLICY CLAUSES (RAG)", s_section))

    raw_clauses = [c.strip() for c in policy_clauses_raw.split("\n\n") if c.strip()]
    if raw_clauses:
        for i, clause in enumerate(raw_clauses, 1):
            clause_block = KeepTogether([
                Paragraph(f"Retrieved Clause {i}", s_clause_hdr),
                Paragraph(clause.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), s_clause),
                Spacer(1, 0.2 * cm),
            ])
            story.append(clause_block)
    else:
        story.append(Paragraph(
            "No policy clauses were retrieved from the vector store for this evaluation.",
            s_body,
        ))

    # ── Section 4: AI Reasoning ───────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_RULE_LINE, spaceBefore=8, spaceAfter=8))
    story.append(Paragraph("SECTION 4 — AI DECISION REASONING", s_section))
    story.append(Paragraph(
        ai_reasoning.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
        s_body,
    ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_RULE_LINE))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        f"Generated by Trace: Enterprise AI Underwriter &nbsp;·&nbsp; IBM watsonx.ai (Mistral Large) "
        f"&nbsp;·&nbsp; {generated_at} &nbsp;·&nbsp; This document is for internal underwriting use only.",
        s_footer,
    ))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------
def show_dashboard() -> None:

    user_email = st.session_state.get("user_email", "")

    # ── Hero ────────────────────────────────────────────────────────────────
    # Two columns: hero HTML fills the wide left col; Sign Out sits in the
    # narrow right col, styled to look like it's inside the banner.
    st.markdown("""
    <style>
        /* Remove gap + padding between the two hero columns */
        div[data-testid="stHorizontalBlock"]:has(div.hero) {
            gap: 0 !important;
            align-items: center !important;
            background: #0a0f1e;
            border-bottom: 1px solid rgba(255,255,255,0.07);
            padding-right: 2.8rem;
            margin-bottom: 2rem;
        }
        /* Target Sign Out button by its key */
        div[data-testid="stButton"]:has(button[kind="secondary"]) button,
        button[data-testid="stBaseButton-secondary"] {
            background: transparent !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: #64748b !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.04em !important;
            padding: 0.38rem 1rem !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            width: auto !important;
            white-space: nowrap !important;
            transition: border-color 0.15s, color 0.15s !important;
        }
        button[data-testid="stBaseButton-secondary"]:hover {
            border-color: rgba(239,68,68,0.4) !important;
            color: #fca5a5 !important;
            background: transparent !important;
            transform: none !important;
            filter: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    hero_col, signout_col = st.columns([9, 1])
    with hero_col:
        st.markdown("""
        <div class="hero" style="border-bottom:none;margin-bottom:0">
            <div class="hero-inner">
                <div class="hero-left">
                    <div class="hero-logo">🛡️</div>
                    <div class="hero-title-group">
                        <h1>Trace: Enterprise AI Underwriter</h1>
                        <p>Actuarial claim evaluation &amp; fraud detection · IBM watsonx.ai</p>
                    </div>
                </div>
                <div class="hero-right">
                    <div class="hero-status-pill">
                        <div class="hero-status-dot"></div>
                        System Operational
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with signout_col:
        if st.button("Sign Out", key="signout_btn", type="secondary"):
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
            '<div class="ph-icon"></div>'
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
                f"{_BACKEND_URL}/api/v1/evaluate-claim",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=90,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error(
                f"❌ Cannot connect to the backend at `{_BACKEND_URL}`. "
                "If running locally, start the FastAPI server first: "
                "`backend\\.venv\\Scripts\\python.exe backend\\run.py`"
            )
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
    risk_score:            float = result["risk_score"]
    recommendation:        str   = result["recommendation"]
    ai_reasoning:          str   = result["ai_reasoning"]
    flagged_anomalies:     list  = result.get("flagged_anomalies", [])
    policy_clauses_raw:    str   = result.get("policy_clauses") or ""
    requires_manual_audit: bool  = result.get("requires_manual_audit", False)
    audit_reason:          str   = result.get("audit_reason") or ""
    rec_lower = recommendation.lower()

    # ── Results heading ───────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.14em;'
        'text-transform:uppercase;color:#374151;margin-bottom:1rem">'
        'Evaluation Results</div>',
        unsafe_allow_html=True,
    )

    # ── Guardrail: manual audit banner ───────────────────────────────────────
    if requires_manual_audit:
        st.markdown(
            f'<div class="audit-banner">'
            f'<div class="audit-banner-icon">⚠️</div>'
            f'<div class="audit-banner-body">'
            f'<div class="audit-banner-title">Low Confidence — Manual Human Audit Required</div>'
            f'<div class="audit-banner-msg">'
            f'The AI evaluation below was generated without sufficient grounding in specific '
            f'internal policy rules. This automated decision <strong>must not be actioned</strong> '
            f'without independent review by a qualified underwriter.'
            f'</div>'
            f'<div class="audit-banner-reason">Reason: {audit_reason}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Verdict card ─────────────────────────────────────────────────────────
    score_pct    = int(risk_score * 100)
    circumference = 2 * 3.14159 * 30          # r=30 → C ≈ 188.5
    dash_offset   = circumference * (1 - risk_score)

    if "approve" in rec_lower:
        verdict_cls   = "verdict-approve"
        chip_label    = "Approved"
        verdict_sub   = "Claim cleared for processing. No significant actuarial risk flags were detected."
    elif "escalate" in rec_lower:
        verdict_cls   = "verdict-escalate"
        chip_label    = "Escalation Required"
        verdict_sub   = "This claim requires review by a Senior Underwriter before any disbursement is authorised."
    else:
        verdict_cls   = "verdict-reject"
        chip_label    = "Rejected"
        verdict_sub   = "Claim does not meet approval criteria. Refer to flagged anomalies for details."

    st.markdown(f"""
    <div class="verdict-card {verdict_cls}">
        <div class="verdict-accent"></div>
        <div class="verdict-content">
            <div class="verdict-body">
                <div class="verdict-chip">
                    <div class="verdict-chip-dot"></div>
                    {chip_label}
                </div>
                <div class="verdict-decision">{recommendation}</div>
                <div class="verdict-sub">{verdict_sub}</div>
            </div>
        </div>
        <div class="verdict-divider"></div>
        <div class="verdict-score-section">
            <div class="verdict-ring-wrap">
                <svg width="72" height="72" viewBox="0 0 72 72">
                    <circle class="verdict-ring-bg" cx="36" cy="36" r="30"/>
                    <circle class="verdict-ring-fill"
                            cx="36" cy="36" r="30"
                            stroke-dasharray="{circumference:.1f}"
                            stroke-dashoffset="{dash_offset:.1f}"/>
                </svg>
                <div class="verdict-ring-label">{score_pct}%</div>
            </div>
            <div class="verdict-score-caption">Risk Score</div>
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

    # ── PDF Audit Report Export ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.14em;'
        'text-transform:uppercase;color:#374151;margin-bottom:0.6rem">'
        'Export</div>',
        unsafe_allow_html=True,
    )
    try:
        pdf_bytes = _build_audit_pdf(
            claim_id              = claim_id,
            policy_id             = claim_policy_id,
            age                   = int(age),
            annual_income         = float(annual_income),
            claim_amount          = float(claim_amount),
            months_since_inception= int(months_since_inception),
            diagnosis_codes       = parse_list(diagnosis_codes_raw),
            medical_history       = parse_list(medical_history_raw),
            risk_score            = risk_score,
            recommendation        = recommendation,
            flagged_anomalies     = flagged_anomalies,
            ai_reasoning          = ai_reasoning,
            policy_clauses_raw    = policy_clauses_raw,
            requires_manual_audit = requires_manual_audit,
            audit_reason          = audit_reason,
        )
        st.download_button(
            label="📄  Download Underwriting Audit Summary (PDF)",
            data=pdf_bytes,
            file_name=f"audit_{claim_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as pdf_exc:
        st.warning(f"PDF generation failed: {pdf_exc}")

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
