import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
load_dotenv()  # loads backend/.env before anything else reads os.environ

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.ai_engine import InsuranceRiskEvaluator
from app.auth import init_jwks, verify_token
from app.db import get_supabase, init_supabase
from app.models import ClaimSubmission, PolicyholderProfile, RiskEvaluationReport

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request body schema  ── wraps both input models into a single JSON payload
# ---------------------------------------------------------------------------
class EvaluateClaimRequest(BaseModel):
    claim: ClaimSubmission
    profile: PolicyholderProfile


# ---------------------------------------------------------------------------
# Lifespan – build the evaluator ONCE at startup so IBM auth only runs once
# ---------------------------------------------------------------------------
_evaluator: InsuranceRiskEvaluator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _evaluator
    logger.info("Initialising InsuranceRiskEvaluator …")
    _evaluator = InsuranceRiskEvaluator()
    logger.info("InsuranceRiskEvaluator ready.")
    logger.info("Initialising Supabase client …")
    init_supabase()
    logger.info("Supabase client ready.")
    logger.info("Fetching Supabase JWKS public key …")
    init_jwks()
    logger.info("JWKS ready.")
    yield
    # nothing to tear down – stateless LLM client / Supabase HTTP client
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Insurance AI Orchestrator",
    description="Life insurance risk evaluation powered by IBM Granite.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS  ── allow the frontend (any localhost port during dev + production origin)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React / Next.js dev server
        "http://localhost:5173",   # Vite dev server
        "http://localhost:8080",   # Vue / generic
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", summary="Health check", tags=["Health"])
def health_check() -> dict:
    """Returns 200 OK when the service is running."""
    return {"status": "ok", "service": "insurance-ai-orchestrator"}


@app.post(
    "/api/v1/evaluate-claim",
    response_model=RiskEvaluationReport,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a life insurance claim for risk",
    tags=["Risk Evaluation"],
)
def evaluate_claim(
    payload: EvaluateClaimRequest,
    _user: dict = Depends(verify_token),
) -> RiskEvaluationReport:
    """
    Accepts a **ClaimSubmission** and a **PolicyholderProfile**, runs them
    through IBM Granite via the InsuranceRiskEvaluator, and returns a
    structured **RiskEvaluationReport** containing:

    - `risk_score` – float 0.0 (safe) → 1.0 (high risk / fraud)
    - `flagged_anomalies` – list of detected red flags
    - `recommendation` – `Approve` | `Escalate to Underwriter` | `Reject`
    - `ai_reasoning` – concise explanation from the model
    """
    try:
        if not _evaluator:
            raise HTTPException(status_code=503, detail="AI Engine not Initialized")

        report = _evaluator.evaluate(claim=payload.claim, profile=payload.profile)

        # ------------------------------------------------------------------ #
        # Persist the evaluation result to Supabase                           #
        # ------------------------------------------------------------------ #
        try:
            get_supabase().table("evaluations").insert(
                {
                    "claim_id": report.claim_id,
                    "policy_id": payload.claim.policy_id,
                    "risk_score": report.risk_score,
                    "recommendation": report.recommendation,
                    "flagged_anomalies": report.flagged_anomalies,
                    "ai_reasoning": report.ai_reasoning,
                }
            ).execute()
            logger.info("Evaluation for claim %s persisted to Supabase.", report.claim_id)
        except Exception as db_exc:
            # Log and continue — a DB write failure must not block the API response
            logger.error(
                "Failed to persist evaluation for claim %s to Supabase: %s",
                report.claim_id,
                db_exc,
            )

        return report

    except ValueError as exc:
        # LLM returned malformed / unparseable output
        logger.error("Evaluation parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI model returned an invalid response: {exc}",
        ) from exc
    except RuntimeError as exc:
        # IBM watsonx API call failed (auth, network, quota …)
        logger.error("Watsonx API error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {exc}",
        ) from exc
