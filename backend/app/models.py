from pydantic import BaseModel
from typing import List, Optional


# 1. The Customer's Background
class PolicyholderProfile(BaseModel):
    policy_id: str
    age: int
    annual_income: float
    medical_history_flags: List[str]  # e.g., ["hypertension", "smoker"]


# 2. The Incoming Claim Data
class ClaimSubmission(BaseModel):
    claim_id: str
    policy_id: str
    claim_amount: float
    months_since_inception: int  # Crucial for detecting early claims
    diagnosis_codes: List[str]


# 3. What the AI will output after reviewing the claim
class RiskEvaluationReport(BaseModel):
    claim_id: str
    risk_score: float  # A mathematical score from 0.0 (safe) to 1.0 (fraud/high risk)
    flagged_anomalies: List[str]
    recommendation: str  # "Approve", "Escalate to Underwriter", or "Reject"
    ai_reasoning: str
    policy_clauses: Optional[str] = None       # Raw RAG-retrieved policy text for traceability
    requires_manual_audit: bool = False        # True when RAG context is too weak to trust automated verdict
    audit_reason: Optional[str] = None        # Human-readable explanation of why audit was triggered
