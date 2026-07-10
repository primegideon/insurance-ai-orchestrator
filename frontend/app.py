"""
Insurance AI Orchestrator – Streamlit frontend
Connects to the FastAPI backend at http://localhost:8000
"""

import streamlit as st
import requests

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Insurance AI Risk Underwriter",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* ── Hero header ── */
    .hero {
        background: linear-gradient(135deg, #0f2645 0%, #1a4a8a 60%, #00AEEF 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,174,239,0.18);
    }
    .hero h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.01em;
    }
    .hero p {
        color: #a8d8f0;
        font-size: 0.95rem;
        margin: 0;
    }
    .hero .badge {
        display: inline-block;
        background: rgba(0,174,239,0.25);
        border: 1px solid rgba(0,174,239,0.5);
        color: #00AEEF;
        border-radius: 999px;
        padding: 0.2rem 0.85rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-top: 0.6rem;
        letter-spacing: 0.04em;
    }

    /* ── Section headers ── */
    .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #00AEEF;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0,174,239,0.2);
    }

    /* ── Evaluate button ── */
    div.stButton > button {
        background: linear-gradient(90deg, #0072C6, #00AEEF) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 4px 18px rgba(0,174,239,0.35) !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #005fa3, #0099d4) !important;
        box-shadow: 0 6px 24px rgba(0,174,239,0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Result cards ── */
    .result-card {
        background: #1E2127;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.07);
    }
    .result-card-title {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 0.6rem;
    }

    /* ── Anomaly pills ── */
    .pill {
        display: inline-block;
        background: rgba(239,68,68,0.15);
        color: #f87171;
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 999px;
        padding: 0.25rem 0.85rem;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.2rem 0.2rem 0.2rem 0;
    }
    .pill-clean {
        display: inline-block;
        background: rgba(16,185,129,0.12);
        color: #34d399;
        border: 1px solid rgba(16,185,129,0.25);
        border-radius: 999px;
        padding: 0.25rem 0.85rem;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* ── AI reasoning box ── */
    .reasoning {
        background: rgba(0,174,239,0.05);
        border-left: 3px solid #00AEEF;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        color: #d1d5db;
        font-size: 0.92rem;
        line-height: 1.7;
    }

    /* ── Divider ── */
    hr { border-color: rgba(255,255,255,0.07) !important; }

    /* ── Metric overrides ── */
    [data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
    }

    /* ── Input labels ── */
    label { font-size: 0.85rem !important; color: #9ca3af !important; }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]

# ---------------------------------------------------------------------------
# Two-column form layout
# ---------------------------------------------------------------------------
form_left, form_right = st.columns(2, gap="large")

with form_left:
    st.markdown('<div class="section-title">📋 Claim Submission</div>', unsafe_allow_html=True)

    claim_id = st.text_input("Claim ID", value="CLM-001", placeholder="CLM-001")
    claim_policy_id = st.text_input("Policy ID", value="POL-777", placeholder="POL-777", key="cpid")
    claim_amount = st.number_input("Claim Amount ($)", min_value=0.0, value=150000.0, step=1000.0, format="%.2f")
    months_since_inception = st.number_input("Months Since Policy Inception", min_value=0, max_value=600, value=5, step=1)
    diagnosis_codes_raw = st.text_input(
        "Diagnosis Codes (comma-separated)",
        value="I21.9",
        placeholder="I21.9, E11, J45",
        help="ICD-10 codes separated by commas",
    )

with form_right:
    st.markdown('<div class="section-title">👤 Policyholder Profile</div>', unsafe_allow_html=True)

    profile_policy_id = st.text_input("Policy ID", value="POL-777", placeholder="POL-777", key="ppid",
                                       help="Must match the Policy ID in the claim")
    age = st.number_input("Age", min_value=18, max_value=110, value=45, step=1)
    annual_income = st.number_input("Annual Income ($)", min_value=0.0, value=25000.0, step=500.0, format="%.2f")
    medical_history_raw = st.text_input(
        "Medical History Flags (comma-separated)",
        value="hypertension",
        placeholder="hypertension, smoker, diabetes",
        help="Leave blank if no prior conditions",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Centred evaluate button ──────────────────────────────────────────────────
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    evaluate_btn = st.button("⚡ Evaluate Risk", use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if not evaluate_btn:
    st.markdown(
        '<div style="text-align:center;color:#6b7280;padding:2.5rem 0;font-size:0.95rem">'
        '📊 Fill in the form above and click <strong style="color:#00AEEF">Evaluate Risk</strong> '
        'to run the AI analysis.'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    payload = {
        "claim": {
            "claim_id": claim_id.strip(),
            "policy_id": claim_policy_id.strip(),
            "claim_amount": float(claim_amount),
            "months_since_inception": int(months_since_inception),
            "diagnosis_codes": parse_list(diagnosis_codes_raw),
        },
        "profile": {
            "policy_id": profile_policy_id.strip(),
            "age": int(age),
            "annual_income": float(annual_income),
            "medical_history_flags": parse_list(medical_history_raw),
        },
    }

    with st.spinner("🤖 Sending to IBM watsonx AI — this may take a few seconds…"):
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/evaluate-claim",
                json=payload,
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

    # ── Recommendation banner ────────────────────────────────────────────────
    st.markdown("### 📊 Evaluation Results")

    if "approve" in rec_lower:
        st.success(f"✅  **{recommendation}** — Claim cleared for processing.")
    elif "escalate" in rec_lower:
        st.warning(f"⚠️  **{recommendation}** — Manual review required before proceeding.")
    else:
        st.error(f"🚫  **{recommendation}** — Claim does not meet approval criteria.")

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
