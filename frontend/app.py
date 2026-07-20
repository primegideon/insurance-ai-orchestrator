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
# Supabase client (reads SUPABASE_URL / SUPABASE_KEY from env or st.secrets)
# ---------------------------------------------------------------------------
def _get_secret(key: str) -> str:
    """Read a config value from env vars first, then st.secrets if present."""
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
# Custom CSS  ── shared between login screen and dashboard
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── 1. Hide Streamlit chrome ── */
    #MainMenu  { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* ── Full-page subtle gradient backdrop ── */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse at 20% 0%, rgba(0,114,198,0.18) 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 100%, rgba(0,174,239,0.12) 0%, transparent 55%),
                    #0E1117;
    }
    [data-testid="stMain"] { background: transparent; }

    /* ── Hero header ── */
    .hero {
        background: linear-gradient(135deg, #0a1a35 0%, #0f2d5e 45%, #0072C6 80%, #00AEEF 100%);
        border-radius: 20px;
        padding: 2.2rem 2.8rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 40px rgba(0,114,198,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -40%; right: -10%;
        width: 420px; height: 420px;
        background: radial-gradient(circle, rgba(0,174,239,0.18) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 12px rgba(0,0,0,0.3);
    }
    .hero p { color: #a8d8f0; font-size: 0.95rem; margin: 0; }
    .hero .badge {
        display: inline-block;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.18);
        color: #e0f4ff;
        border-radius: 999px;
        padding: 0.22rem 0.9rem;
        font-size: 0.76rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-top: 0.65rem;
        letter-spacing: 0.04em;
    }

    /* ── Login card — target the native Streamlit form container ── */
    [data-testid="stForm"] {
        background: rgba(10, 14, 26, 0.80) !important;
        border: 2px solid transparent !important;
        border-radius: 20px !important;
        padding: 2rem 2rem 1.6rem !important;
        backdrop-filter: blur(28px) !important;
        -webkit-backdrop-filter: blur(28px) !important;
        background-clip: padding-box !important;
        box-shadow:
            0 0 0 2px rgba(0,174,239,0.55),
            0 8px 48px rgba(0,114,198,0.40),
            0 2px 80px rgba(0,174,239,0.15) !important;
        margin-top: 0.5rem !important;
    }

    /* Form submit button — identical gradient to Evaluate Risk */
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #0072C6 0%, #00AEEF 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        box-shadow: 0 4px 20px rgba(0,174,239,0.45), inset 0 1px 0 rgba(255,255,255,0.15) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(90deg, #0072C6 0%, #00AEEF 100%) !important;
        box-shadow: 0 6px 32px rgba(0,174,239,0.75), inset 0 1px 0 rgba(255,255,255,0.22) !important;
        transform: translateY(-2px) !important;
        filter: brightness(1.15) !important;
    }
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0) !important;
        filter: brightness(1) !important;
    }

    /* ── 2. Glassmorphism input widgets ── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #f0f4f8 !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
        backdrop-filter: blur(6px) !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #00AEEF !important;
        box-shadow: 0 0 0 3px rgba(0, 174, 239, 0.2), 0 0 16px rgba(0, 174, 239, 0.12) !important;
        outline: none !important;
    }
    /* number input spinner buttons */
    [data-testid="stNumberInput"] button {
        background: rgba(255,255,255,0.06) !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: #9ca3af !important;
    }

    /* ── Section headers ── */
    .section-title {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #00AEEF;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0,174,239,0.2);
    }

    /* ── Evaluate / Login buttons ── */
    div.stButton > button {
        background: linear-gradient(90deg, #0072C6 0%, #00AEEF 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        box-shadow: 0 4px 20px rgba(0,174,239,0.4), inset 0 1px 0 rgba(255,255,255,0.15) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #0072C6 0%, #00AEEF 100%) !important;
        box-shadow: 0 6px 32px rgba(0,174,239,0.75), inset 0 1px 0 rgba(255,255,255,0.22) !important;
        transform: translateY(-2px) !important;
        filter: brightness(1.15) !important;
    }
    div.stButton > button:active { transform: translateY(0) !important; }

    /* ── 3. Glassmorphism metric cards ── */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 14px !important;
        padding: 1.1rem 1.2rem !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        transition: box-shadow 0.2s !important;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 6px 32px rgba(0,174,239,0.18), inset 0 1px 0 rgba(255,255,255,0.06) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: #6b7280 !important;
    }

    /* ── 4. Custom verdict banners ── */
    .verdict-approve {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 60%, #047857 100%);
        border: 1px solid rgba(16,185,129,0.4);
        border-radius: 14px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 4px 24px rgba(16,185,129,0.2), inset 0 1px 0 rgba(255,255,255,0.07);
    }
    .verdict-escalate {
        background: linear-gradient(135deg, #451a03 0%, #78350f 60%, #92400e 100%);
        border: 1px solid rgba(245,158,11,0.4);
        border-radius: 14px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 4px 24px rgba(245,158,11,0.18), inset 0 1px 0 rgba(255,255,255,0.07);
    }
    .verdict-reject {
        background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 60%, #991b1b 100%);
        border: 1px solid rgba(239,68,68,0.4);
        border-radius: 14px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 4px 24px rgba(239,68,68,0.2), inset 0 1px 0 rgba(255,255,255,0.07);
    }
    .verdict-icon  { font-size: 1.6rem; margin-bottom: 0.3rem; line-height: 1; }
    .verdict-label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
                     text-transform: uppercase; color: rgba(255,255,255,0.55); margin-bottom: 0.15rem; }
    .verdict-text  { font-size: 1.25rem; font-weight: 800; color: #ffffff;
                     letter-spacing: -0.01em; line-height: 1.2; }
    .verdict-sub   { font-size: 0.85rem; color: rgba(255,255,255,0.65); margin-top: 0.3rem; }

    /* ── Anomaly pills ── */
    .pill {
        display: inline-block;
        background: rgba(239,68,68,0.12);
        color: #fca5a5;
        border: 1px solid rgba(239,68,68,0.25);
        border-radius: 999px;
        padding: 0.28rem 0.9rem;
        font-size: 0.79rem;
        font-weight: 500;
        margin: 0.2rem 0.25rem 0.2rem 0;
        backdrop-filter: blur(4px);
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

    /* ── AI reasoning box ── */
    .reasoning {
        background: rgba(0,174,239,0.05);
        border: 1px solid rgba(0,174,239,0.15);
        border-left: 3px solid #00AEEF;
        border-radius: 0 12px 12px 0;
        padding: 1.1rem 1.4rem;
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.75;
        backdrop-filter: blur(6px);
    }

    /* ── Divider ── */
    hr { border: none; border-top: 1px solid rgba(255,255,255,0.06) !important; margin: 0.5rem 0 1.5rem; }

    /* ── Input labels ── */
    label { font-size: 0.82rem !important; color: #8b95a3 !important; font-weight: 500 !important; }

    /* ── Expander glass ── */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def _is_authenticated() -> bool:
    """Return True if a valid session token is stored in st.session_state."""
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
    """Render the centred login card and handle Supabase Auth sign-in."""

    # Centred branding above the card
    st.markdown("""
    <div style="text-align:center;margin-top:2.5rem;margin-bottom:0.5rem">
        <div style="font-size:2.8rem;line-height:1">🛡️</div>
        <div style="color:#ffffff;font-size:1.6rem;font-weight:800;
                    letter-spacing:-0.02em;margin-top:0.5rem">
            Insurance AI Risk Underwriter
        </div>
        <div style="color:#6b7280;font-size:0.88rem;margin-top:0.4rem">
            Sign in to access the underwriting dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Narrow centred column — [1,2,1] keeps the card from spanning too wide
    _, card_col, _ = st.columns([1, 2, 1])
    with card_col:
        # Glowing gradient title — pure st.markdown, no blocked wrappers
        st.markdown(
            """
            <h2 style="
                text-align: center;
                margin: 0 0 1.2rem 0;
                font-size: 1.5rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                background: -webkit-linear-gradient(left, #0072C6, #00AEEF);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                filter: drop-shadow(0 0 12px rgba(0,174,239,0.45));
            ">🔐 Underwriter Portal</h2>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            email    = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter both your email and password.")
                return
            try:
                response = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                _store_session(response.session)
                st.rerun()
            except Exception as exc:
                error_msg = str(exc)
                if "Invalid login credentials" in error_msg or "invalid_credentials" in error_msg:
                    st.error("❌ Incorrect email or password.")
                elif "Email not confirmed" in error_msg:
                    st.error("📧 Please confirm your email address before signing in.")
                else:
                    st.error(f"❌ Sign-in failed: {error_msg}")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------
def show_dashboard() -> None:
    """Render the full insurance AI dashboard (only shown when authenticated)."""

    # ── Hero header with sign-out ────────────────────────────────────────────
    hero_col, signout_col = st.columns([5, 1])
    with hero_col:
        st.markdown("""
        <div class="hero">
            <h1>🛡️ Insurance AI Risk Underwriter</h1>
            <p>Real-time life insurance claim analysis powered by AI</p>
            <div style="margin-top:0.6rem">
                <span class="badge">⚡ IBM watsonx</span>
                <span class="badge">🤖 Mistral Large</span>
                <span class="badge">🔒 Life Insurance</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with signout_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        user_email = st.session_state.get("user_email", "")
        if user_email:
            st.markdown(
                f'<div style="color:#6b7280;font-size:0.78rem;text-align:right;'
                f'margin-bottom:0.4rem">{user_email}</div>',
                unsafe_allow_html=True,
            )
        if st.button("Sign Out", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            _clear_session()
            st.rerun()

    # ── Two-column form layout ───────────────────────────────────────────────
    form_left, form_right = st.columns(2, gap="large")

    with form_left:
        st.markdown('<div class="section-title">📋 Claim Submission</div>', unsafe_allow_html=True)

        claim_id              = st.text_input("Claim ID", value="CLM-001", placeholder="CLM-001")
        claim_policy_id       = st.text_input("Policy ID", value="POL-777", placeholder="POL-777", key="cpid")
        claim_amount          = st.number_input("Claim Amount ($)", min_value=0.0, value=150000.0, step=1000.0, format="%.2f")
        months_since_inception = st.number_input("Months Since Policy Inception", min_value=0, max_value=600, value=5, step=1)
        diagnosis_codes_raw   = st.text_input(
            "Diagnosis Codes (comma-separated)",
            value="I21.9",
            placeholder="I21.9, E11, J45",
            help="ICD-10 codes separated by commas",
        )

    with form_right:
        st.markdown('<div class="section-title">👤 Policyholder Profile</div>', unsafe_allow_html=True)

        profile_policy_id = st.text_input("Policy ID", value="POL-777", placeholder="POL-777", key="ppid",
                                           help="Must match the Policy ID in the claim")
        age            = st.number_input("Age", min_value=18, max_value=110, value=45, step=1)
        annual_income  = st.number_input("Annual Income ($)", min_value=0.0, value=25000.0, step=500.0, format="%.2f")
        medical_history_raw = st.text_input(
            "Medical History Flags (comma-separated)",
            value="hypertension",
            placeholder="hypertension, smoker, diabetes",
            help="Leave blank if no prior conditions",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Centred evaluate button ──────────────────────────────────────────────
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        evaluate_btn = st.button("⚡ Evaluate Risk", use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Results ─────────────────────────────────────────────────────────────
    if not evaluate_btn:
        st.markdown(
            '<div style="text-align:center;color:#6b7280;padding:2.5rem 0;font-size:0.95rem">'
            '📊 Fill in the form above and click <strong style="color:#00AEEF">Evaluate Risk</strong> '
            'to run the AI analysis.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    payload = {
        "claim": {
            "claim_id":              claim_id.strip(),
            "policy_id":             claim_policy_id.strip(),
            "claim_amount":          float(claim_amount),
            "months_since_inception": int(months_since_inception),
            "diagnosis_codes":       parse_list(diagnosis_codes_raw),
        },
        "profile": {
            "policy_id":             profile_policy_id.strip(),
            "age":                   int(age),
            "annual_income":         float(annual_income),
            "medical_history_flags": parse_list(medical_history_raw),
        },
    }

    access_token = st.session_state["access_token"]

    with st.spinner("🤖 Sending to IBM watsonx AI — this may take a few seconds…"):
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

    # ── Unpack ──────────────────────────────────────────────────────────────
    risk_score: float       = result["risk_score"]
    recommendation: str     = result["recommendation"]
    ai_reasoning: str       = result["ai_reasoning"]
    flagged_anomalies: list = result.get("flagged_anomalies", [])
    rec_lower               = recommendation.lower()

    # ── Custom verdict banner ────────────────────────────────────────────────
    st.markdown("### 📊 Evaluation Results")

    if "approve" in rec_lower:
        st.markdown(f"""
        <div class="verdict-approve">
            <div class="verdict-icon">✅</div>
            <div class="verdict-label">Verdict</div>
            <div class="verdict-text">{recommendation}</div>
            <div class="verdict-sub">Claim cleared for processing — no significant risk flags detected.</div>
        </div>
        """, unsafe_allow_html=True)
    elif "escalate" in rec_lower:
        st.markdown(f"""
        <div class="verdict-escalate">
            <div class="verdict-icon">⚠️</div>
            <div class="verdict-label">Verdict</div>
            <div class="verdict-text">{recommendation}</div>
            <div class="verdict-sub">Manual underwriter review required before this claim can proceed.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="verdict-reject">
            <div class="verdict-icon">🚫</div>
            <div class="verdict-label">Verdict</div>
            <div class="verdict-text">{recommendation}</div>
            <div class="verdict-sub">Claim does not meet approval criteria — refer to anomalies below.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Key metrics row ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    score_pct = int(risk_score * 100)
    if risk_score < 0.4:
        score_delta, delta_color = "Low risk", "normal"
    elif risk_score < 0.7:
        score_delta, delta_color = "Medium risk", "off"
    else:
        score_delta, delta_color = "High risk", "inverse"

    with m1:
        st.metric(
            label="🎯 Risk Score",
            value=f"{risk_score:.2f}",
            delta=score_delta,
            delta_color=delta_color,
        )
    with m2:
        st.metric(
            label="🚩 Anomalies",
            value=str(len(flagged_anomalies)),
            delta="flags detected" if flagged_anomalies else "all clear",
            delta_color="inverse" if flagged_anomalies else "normal",
        )
    with m3:
        st.metric(
            label="📅 Policy Age",
            value=f"{months_since_inception} mo.",
            delta="Early claim ⚠️" if months_since_inception < 12 else "Normal tenure",
            delta_color="inverse" if months_since_inception < 12 else "normal",
        )
    with m4:
        income_ratio = claim_amount / annual_income if annual_income > 0 else 0
        st.metric(
            label="💰 Claim / Income Ratio",
            value=f"{income_ratio:.1f}×",
            delta="Anti-selection risk" if income_ratio > 5 else "Within range",
            delta_color="inverse" if income_ratio > 5 else "normal",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Bottom two-column detail ─────────────────────────────────────────────
    detail_left, detail_right = st.columns([1, 1], gap="large")

    with detail_left:
        st.markdown('<div class="section-title">🚩 Flagged Anomalies</div>', unsafe_allow_html=True)
        if flagged_anomalies:
            pills = " ".join(f'<span class="pill">{a}</span>' for a in flagged_anomalies)
            st.markdown(f'<div style="margin-top:0.4rem">{pills}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="pill-clean">✓ No anomalies detected</span>', unsafe_allow_html=True)

    with detail_right:
        st.markdown('<div class="section-title">📌 Claim Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-size:0.88rem;color:#9ca3af;line-height:2">
            <b style="color:#d1d5db">Claim ID</b> &nbsp;·&nbsp; {claim_id}<br>
            <b style="color:#d1d5db">Policy ID</b> &nbsp;·&nbsp; {claim_policy_id}<br>
            <b style="color:#d1d5db">Claimant Age</b> &nbsp;·&nbsp; {age} yrs<br>
            <b style="color:#d1d5db">Claim Amount</b> &nbsp;·&nbsp; ${claim_amount:,.2f}<br>
            <b style="color:#d1d5db">Annual Income</b> &nbsp;·&nbsp; ${annual_income:,.2f}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI Reasoning ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🤖 AI Reasoning</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="reasoning">{ai_reasoning}</div>', unsafe_allow_html=True)

    # ── Raw JSON ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔍 Raw API Response"):
        st.json(result)


# ---------------------------------------------------------------------------
# Entry point  ── auth gate
# ---------------------------------------------------------------------------
if _is_authenticated():
    show_dashboard()
else:
    show_login()
