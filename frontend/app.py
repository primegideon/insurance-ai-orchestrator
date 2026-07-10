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
# Custom CSS – minimal, professional
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Top header bar */
        .header-bar {
            background: #1e3a5f;
            padding: 1.1rem 1.6rem;
            border-radius: 8px;
            margin-bottom: 1.6rem;
        }
        .header-bar h1 {
            color: #ffffff;
            margin: 0;
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        .header-bar p {
            color: #a8c4e0;
            margin: 0.2rem 0 0;
            font-size: 0.9rem;
        }

        /* Section card */
        .card {
            background: #f7f8fa;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 1rem;
        }
        .card h3 {
            margin-top: 0;
            font-size: 1rem;
            color: #1e3a5f;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 0.5rem;
        }

        /* Result band */
        .result-approve  { background:#d1fae5; border-left:5px solid #10b981; padding:1rem 1.2rem; border-radius:6px; }
        .result-escalate { background:#fef3c7; border-left:5px solid #f59e0b; padding:1rem 1.2rem; border-radius:6px; }
        .result-reject   { background:#fee2e2; border-left:5px solid #ef4444; padding:1rem 1.2rem; border-radius:6px; }

        /* Anomaly pills */
        .pill {
            display:inline-block;
            background:#fee2e2;
            color:#991b1b;
            border-radius:999px;
            padding:0.2rem 0.75rem;
            font-size:0.82rem;
            margin:0.2rem 0.2rem 0.2rem 0;
            font-weight:500;
        }
        .pill-none {
            display:inline-block;
            background:#d1fae5;
            color:#065f46;
            border-radius:999px;
            padding:0.2rem 0.75rem;
            font-size:0.82rem;
        }

        /* Score gauge text */
        .score-value { font-size:2.8rem; font-weight:700; line-height:1; }
        .score-low  { color:#10b981; }
        .score-mid  { color:#f59e0b; }
        .score-high { color:#ef4444; }

        /* Reasoning box */
        .reasoning-box {
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-radius:6px;
            padding:0.9rem 1rem;
            font-size:0.93rem;
            line-height:1.65;
            color:#374151;
        }

        /* Hide Streamlit branding */
        #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="header-bar">
        <h1>🛡️ Insurance AI Risk Underwriter</h1>
        <p>Powered by IBM watsonx · Mistral Large · Life Insurance Claims Analysis</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Layout: form (left) | results (right)
# ---------------------------------------------------------------------------
left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    # ── Claim Submission ────────────────────────────────────────────────────
    st.markdown('<div class="card"><h3>📋 Claim Submission</h3>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        claim_id = st.text_input("Claim ID", value="CLM-001", placeholder="CLM-001")
    with c2:
        claim_policy_id = st.text_input("Policy ID", value="POL-777", placeholder="POL-777", key="claim_policy_id")

    claim_amount = st.number_input(
        "Claim Amount ($)",
        min_value=0.0, value=150000.0, step=1000.0, format="%.2f"
    )
    months_since_inception = st.number_input(
        "Months Since Policy Inception",
        min_value=0, max_value=600, value=5, step=1
    )
    diagnosis_codes_raw = st.text_input(
        "Diagnosis Codes (comma-separated)",
        value="I21.9",
        placeholder="I21.9, E11, J45",
        help="ICD-10 codes separated by commas"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Policyholder Profile ────────────────────────────────────────────────
    st.markdown('<div class="card"><h3>👤 Policyholder Profile</h3>', unsafe_allow_html=True)

    profile_policy_id = st.text_input(
        "Policy ID", value="POL-777", placeholder="POL-777", key="profile_policy_id",
        help="Must match the Policy ID in the claim above"
    )

    p1, p2 = st.columns(2)
    with p1:
        age = st.number_input("Age", min_value=18, max_value=110, value=45, step=1)
    with p2:
        annual_income = st.number_input(
            "Annual Income ($)",
            min_value=0.0, value=25000.0, step=500.0, format="%.2f"
        )

    medical_history_raw = st.text_input(
        "Medical History Flags (comma-separated)",
        value="hypertension",
        placeholder="hypertension, smoker, diabetes",
        help="Leave blank if no prior conditions"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Submit ──────────────────────────────────────────────────────────────
    evaluate_btn = st.button("⚡ Evaluate Risk", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Results panel
# ---------------------------------------------------------------------------
with right_col:
    st.markdown("#### 📊 Evaluation Results")

    if not evaluate_btn:
        st.info("Fill in the form on the left and click **Evaluate Risk** to run the AI analysis.")
    else:
        # ── Build payload ───────────────────────────────────────────────────
        def _parse_list(raw: str) -> list[str]:
            return [item.strip() for item in raw.split(",") if item.strip()]

        payload = {
            "claim": {
                "claim_id": claim_id.strip(),
                "policy_id": claim_policy_id.strip(),
                "claim_amount": float(claim_amount),
                "months_since_inception": int(months_since_inception),
                "diagnosis_codes": _parse_list(diagnosis_codes_raw),
            },
            "profile": {
                "policy_id": profile_policy_id.strip(),
                "age": int(age),
                "annual_income": float(annual_income),
                "medical_history_flags": _parse_list(medical_history_raw),
            },
        }

        # ── Call the API ────────────────────────────────────────────────────
        with st.spinner("Sending to IBM watsonx AI…"):
            try:
                response = requests.post(
                    "http://localhost:8000/api/v1/evaluate-claim",
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the backend. Is the FastAPI server running on port 8000?")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("⏱️ The request timed out after 60 seconds.")
                st.stop()
            except requests.exceptions.HTTPError as e:
                detail = ""
                try:
                    detail = response.json().get("detail", "")
                except Exception:
                    pass
                st.error(f"❌ API error {response.status_code}: {detail or str(e)}")
                st.stop()

        # ── Render results ──────────────────────────────────────────────────
        risk_score: float = result["risk_score"]
        recommendation: str = result["recommendation"]
        ai_reasoning: str = result["ai_reasoning"]
        flagged_anomalies: list = result.get("flagged_anomalies", [])

        # Recommendation banner
        rec_lower = recommendation.lower()
        if "approve" in rec_lower:
            band_class, icon = "result-approve", "✅"
        elif "escalate" in rec_lower:
            band_class, icon = "result-escalate", "⚠️"
        else:
            band_class, icon = "result-reject", "🚫"

        st.markdown(
            f'<div class="{band_class}"><strong style="font-size:1.1rem">'
            f'{icon} {recommendation}</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        # Metrics row
        m1, m2, m3 = st.columns(3)
        score_pct = int(risk_score * 100)

        if risk_score < 0.4:
            score_class = "score-low"
        elif risk_score < 0.7:
            score_class = "score-mid"
        else:
            score_class = "score-high"

        with m1:
            st.markdown(
                f'<div style="text-align:center">'
                f'<div style="font-size:0.8rem;color:#57606a;margin-bottom:4px">RISK SCORE</div>'
                f'<div class="score-value {score_class}">{risk_score:.2f}</div>'
                f'<div style="font-size:0.8rem;color:#57606a">{score_pct}th percentile risk</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with m2:
            anomaly_count = len(flagged_anomalies)
            a_color = "#ef4444" if anomaly_count > 0 else "#10b981"
            st.markdown(
                f'<div style="text-align:center">'
                f'<div style="font-size:0.8rem;color:#57606a;margin-bottom:4px">ANOMALIES</div>'
                f'<div class="score-value" style="color:{a_color}">{anomaly_count}</div>'
                f'<div style="font-size:0.8rem;color:#57606a">flag(s) detected</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with m3:
            months_label = f"{months_since_inception} mo."
            inception_color = "#ef4444" if months_since_inception < 12 else "#10b981"
            st.markdown(
                f'<div style="text-align:center">'
                f'<div style="font-size:0.8rem;color:#57606a;margin-bottom:4px">POLICY AGE</div>'
                f'<div class="score-value" style="color:{inception_color}">{months_label}</div>'
                f'<div style="font-size:0.8rem;color:#57606a">since inception</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Flagged anomalies
        st.markdown("**🚩 Flagged Anomalies**")
        if flagged_anomalies:
            pills = "".join(f'<span class="pill">{a}</span>' for a in flagged_anomalies)
            st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="pill-none">No anomalies detected</span>', unsafe_allow_html=True)

        st.markdown("")

        # AI reasoning
        st.markdown("**🤖 AI Reasoning**")
        st.markdown(f'<div class="reasoning-box">{ai_reasoning}</div>', unsafe_allow_html=True)

        # Raw JSON expander
        with st.expander("Raw API response"):
            st.json(result)
