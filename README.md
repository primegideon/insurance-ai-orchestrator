# 🛡️ Insurance AI Orchestrator
### IBM AI Builders Challenge — Submission

> **Real-time life insurance claim risk evaluation powered by IBM watsonx.ai and Mistral Large, orchestrated through a FastAPI backend and a premium Streamlit dashboard.**

---

## 📌 Selected Challenge Theme

**Insurance Claims & Risk Workflow Automation**

This project addresses the end-to-end automation of life insurance claim intake, risk scoring, fraud detection, and underwriter decision support — replacing slow, error-prone manual review with an AI-driven evaluation pipeline that delivers a structured verdict in seconds.

---

## 🔍 Problem Statement

Manual life insurance underwriting is a bottleneck that costs the industry billions of dollars annually:

- **Speed** — Senior underwriters can review only a small number of complex claims per day. Queues grow quickly during high-volume periods (e.g. post-pandemic surges).
- **Consistency** — Human reviewers apply rules inconsistently. Fatigue, cognitive bias, and varying experience levels mean identical claims can receive different verdicts depending on who reviews them.
- **Pattern blindness** — Multi-factor fraud patterns are difficult to detect manually. A claim might appear legitimate in isolation, yet reveal clear fraud when the claim amount, policy tenure, diagnosis codes, and policyholder income are evaluated *together*.
- **Specific failure modes** that human reviewers routinely miss:
  - **Financial Anti-Selection** — claimant submits a policy with a benefit far exceeding their ability to have legitimately needed it (claim-to-income ratio > 5×).
  - **Early Claim Fraud** — a major claim filed within the first 12 months of policy inception, a strong indicator the policy was taken out with intent to defraud.
  - **Material Misrepresentation** — a serious condition is claimed with no matching medical history flags declared at application time.
  - **The High-Risk Triangle** — age > 65, policy < 36 months old, and a large claim amount co-occurring simultaneously.

The industry needs a system that applies these rules *holistically*, *every time*, *at scale*.

---

## 💡 Solution Description

**Insurance AI Orchestrator** is a full-stack web application that automates the first-pass underwriting decision for life insurance claims. It works as follows:

1. **An underwriter (or automated intake system) submits** a claim and policyholder profile via a clean web form.
2. **The FastAPI backend** validates the payload, constructs a structured actuarial prompt, and forwards it to IBM watsonx.ai.
3. **The AI model** evaluates the claim holistically against domain-specific underwriting rules and returns a structured JSON verdict containing:
   - `risk_score` — a float from `0.0` (safe) to `1.0` (high-risk / fraud)
   - `flagged_anomalies` — a list of specific red flags detected
   - `recommendation` — one of `Approve`, `Escalate to Underwriter`, or `Reject`
   - `ai_reasoning` — a concise natural-language explanation of the decision
4. **The Streamlit dashboard** renders the verdict instantly with colour-coded banners, glassmorphism metric cards, anomaly pills, and a full reasoning panel.

### Key capabilities

| Feature | Detail |
|---|---|
| Actuarial rule coverage | Financial Anti-Selection, Early Claims, Material Misrepresentation, High-Risk Triangle |
| Structured output enforcement | Backend parses and validates all four JSON fields; malformed LLM responses surface a clean 502 error |
| Verdict categories | `Approve` · `Escalate to Underwriter` · `Reject` |
| Claim/Income ratio live calculation | Computed and displayed in real-time on the dashboard |
| Zero hallucination guard | Recommendation field validated against an explicit allowlist before the response is returned |

---

## 🏗️ Architecture & AI Approach

```
┌──────────────────────────────────────────────────────────────────┐
│                        User (Browser)                            │
│               http://localhost:8501  (Streamlit)                 │
└──────────────────────┬───────────────────────────────────────────┘
                       │  HTTP POST /api/v1/evaluate-claim
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                                │
│                 http://localhost:8000                             │
│                                                                  │
│  • Pydantic models: ClaimSubmission, PolicyholderProfile         │
│  • InsuranceRiskEvaluator  (app/ai_engine.py)                    │
│    ├── Builds ChatPromptTemplate (system + human messages)       │
│    ├── Invokes ChatWatsonx chain                                 │
│    └── Parses + validates structured JSON response               │
└──────────────────────┬───────────────────────────────────────────┘
                       │  LangChain ChatWatsonx  (langchain-ibm)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    IBM watsonx.ai                                 │
│              Model: mistral-large-2512                           │
│                                                                  │
│  • Chat completion endpoint  (/ml/v1/text/chat)                  │
│  • Temperature: 0.0 (deterministic, critical for JSON parsing)   │
│  • Max tokens: 512                                               │
└──────────────────────────────────────────────────────────────────┘
```

### Frontend — Streamlit (`frontend/app.py`)

- **Layout** — Wide two-column form (Claim Submission | Policyholder Profile) with a centred CTA button.
- **Premium glassmorphism CSS** — custom `st.markdown` injections targeting Streamlit's `data-testid` selectors:
  - Input widgets: `rgba(255,255,255,0.05)` backgrounds, `backdrop-filter: blur`, glowing focus rings.
  - Metric cards: frosted glass tiles with `box-shadow` depth and hover lift.
  - Verdict banners: rich gradient `<div>` blocks (deep green / amber / red) replacing `st.success/warning/error`.
  - Full-page radial gradient backdrop.
- **Dark theme** configured via `frontend/.streamlit/config.toml` (`primaryColor: #00AEEF`, `backgroundColor: #0E1117`).
- **4 live metrics** — Risk Score, Anomaly Count, Policy Age, Claim/Income Ratio — all colour-coded by threshold.

### Backend — FastAPI (`backend/app/`)

| File | Responsibility |
|---|---|
| `main.py` | FastAPI app, CORS middleware, `/api/v1/evaluate-claim` endpoint, lifespan startup |
| `ai_engine.py` | `InsuranceRiskEvaluator` class — prompt construction, LLM invocation, JSON parsing & validation |
| `models.py` | Pydantic schemas: `ClaimSubmission`, `PolicyholderProfile`, `RiskEvaluationReport` |
| `run.py` | Convenience launcher — spawns uvicorn from any working directory |

### AI Layer — IBM watsonx.ai

- **Model**: `mistral-large-2512` via the IBM watsonx.ai chat endpoint
  > *Note: The original model target was `ibm/granite-3-1-8b-instruct`. During development it was discovered that this model ID was not available in the target watsonx environment (it does not support the `function_text_generation` endpoint). `mistral-large-2512` was selected as the replacement for its strong instruction-following and structured JSON output capabilities.*
- **Orchestration**: LangChain's `ChatWatsonx` integration (`langchain-ibm`) with a `ChatPromptTemplate` (system + human message pair).
- **Prompt engineering**: The system message establishes the AI as a Senior Life Insurance Underwriter. The human message provides fully structured claim and profile data, explicit detection rules, and a strict JSON output schema. Temperature is locked at `0.0` for deterministic, parseable responses.
- **Output hardening**: The backend strips any markdown code fences the model may emit, then validates all four output fields before returning a response to the frontend.

### Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Streamlit | 1.59.1 |
| Backend | FastAPI + Uvicorn | 0.139.0 / 0.30.1 |
| Data validation | Pydantic | 2.13.4 |
| AI orchestration | LangChain + langchain-ibm | 1.3.x / 1.1.0 |
| IBM AI SDK | ibm-watsonx-ai | 1.5.14 |
| LLM | Mistral Large (via watsonx.ai) | mistral-large-2512 |
| Language | Python | 3.12 |

---

## 🤖 How IBM Bob Was Used

Bob (IBM's AI coding assistant) was an active pair-programmer throughout this project, not just a code generator. Key contributions:

### 1 — FastAPI Server Scaffolding
Bob designed and wrote the entire backend architecture from scratch:
- The three-layer model structure (`ClaimSubmission` → `InsuranceRiskEvaluator` → `RiskEvaluationReport`)
- The FastAPI lifespan pattern to initialise the LLM client once at startup (avoiding repeated IBM auth overhead on every request)
- The CORS middleware configuration for local Streamlit ↔ FastAPI communication
- Structured error handling — separating `ValueError` (malformed LLM output → 502) from `RuntimeError` (watsonx API failure → 503)

### 2 — Debugging Complex Python Dependency Conflicts
During development, a critical version conflict emerged when Streamlit was installed into the backend virtual environment:

- **Root cause**: `streamlit>=1.35` requires `starlette>=0.40.0`, but `fastapi==0.111.0` (the original pinned version) caps starlette at `<0.38.0`.
- **Bob's resolution**: Identified the conflict from the pip error output, diagnosed that upgrading FastAPI to `>=0.115.0` resolves the starlette constraint on both sides, and executed the fix — upgrading FastAPI to `0.139.0` with a compatible pydantic/pydantic-core pair — all without disrupting the existing backend code.
- **Model endpoint mismatch**: Also debugged a `model_no_support_for_function` error where `WatsonxLLM` (text generation) was used with a chat-only model. Bob identified the correct LangChain class (`ChatWatsonx`), rewrote the chain to use `ChatPromptTemplate` with system/human message pairs, and updated the parameter names (`max_tokens` vs `max_new_tokens`).

### 3 — Custom CSS to Override Streamlit's Default Styling
Streamlit's default UI components cannot be restyled through Python alone. Bob wrote all custom CSS injected via `st.markdown(..., unsafe_allow_html=True)`:
- Discovered and targeted Streamlit's internal `data-testid` attribute selectors (e.g. `[data-testid="stMetric"]`, `[data-testid="stTextInput"]`) to apply glassmorphism styling without breaking Streamlit's component rendering
- Implemented the full glassmorphism design system: semi-transparent backgrounds, `backdrop-filter: blur`, layered `box-shadow` depth, glowing focus rings, and gradient verdict banners
- Correctly separated the three Streamlit chrome-hiding rules (`#MainMenu`, `footer`, `header`) as individual declarations to ensure all three are suppressed

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- An IBM Cloud account with a watsonx.ai project
- `WATSONX_API_KEY`, `WATSONX_URL`, and `WATSONX_PROJECT_ID`

### Environment Setup

Create `backend/.env`:

```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=your_watsonx_project_id
```

### Installation

```powershell
# From the repo root — one virtual environment for everything
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### Running the Application

**Terminal 1 — Backend:**
```powershell
# From the repo root
backend\.venv\Scripts\python.exe backend\run.py
```

**Terminal 2 — Frontend:**
```powershell
# From the repo root
backend\.venv\Scripts\streamlit.exe run frontend\app.py
```

Then open **http://localhost:8501** in your browser. The FastAPI docs are available at **http://localhost:8000/docs**.

### Project Structure

```
insurance-ai-orchestrator/
├── backend/
│   ├── app/
│   │   ├── ai_engine.py        # InsuranceRiskEvaluator — LLM chain & JSON parsing
│   │   ├── main.py             # FastAPI app, routes, CORS, lifespan
│   │   ├── models.py           # Pydantic schemas
│   │   └── __init__.py
│   ├── tests/
│   ├── .env                    # IBM credentials (git-ignored)
│   ├── requirements.txt
│   └── run.py                  # Uvicorn launcher
└── frontend/
    ├── .streamlit/
    │   └── config.toml         # Dark theme configuration
    ├── app.py                  # Streamlit dashboard
    └── requirements.txt
```

---

## 📄 License

MIT — see `LICENSE` for details.

---

*Submitted for the IBM AI Builders Challenge · July 2026*
