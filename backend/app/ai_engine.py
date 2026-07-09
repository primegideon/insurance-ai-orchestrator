import json
import logging
import os
from typing import Any

from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from pydantic import SecretStr
from langchain_ibm import WatsonxLLM
from langchain_core.prompts import PromptTemplate

from app.models import ClaimSubmission, PolicyholderProfile, RiskEvaluationReport

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
_RISK_EVAL_TEMPLATE = """\
You are an expert life insurance underwriting AI. Your task is to evaluate \
a submitted claim and the associated policyholder profile for risk and \
potential fraud.

## Policyholder Profile
- Policy ID          : {policy_id}
- Age                : {age}
- Annual Income      : ${annual_income:,.2f}
- Medical History    : {medical_history_flags}

## Claim Submission
- Claim ID                  : {claim_id}
- Claim Amount              : ${claim_amount:,.2f}
- Months Since Policy Start : {months_since_inception}
- Diagnosis Codes           : {diagnosis_codes}

## Instructions
Analyze the above data holistically like a Senior Life Insurance Underwriter. Flag the claim and recommend "Escalate to Underwriter" or "Reject" if you detect any of the following:
- Financial Anti-Selection: The claim_amount is suspiciously high compared to the annual_income (e.g., > 5x their income).
- Material Misrepresentation: A major medical claim is made within the first 24 months, but the medical_history_flags show no relevant pre-existing conditions.
- The High-Risk Triangle: The policyholder is older than 65, the months_since_inception is under 36, and the claim amount is high.
- Early Claims: Any claim made where months_since_inception < 12.

Return your analysis **only** as a valid JSON object — no markdown fences, \
no extra text — with exactly these keys:

{{
  "risk_score": <float 0.0–1.0>,
  "flagged_anomalies": [<string>, ...],
  "recommendation": "<Approve|Escalate to Underwriter|Reject>",
  "ai_reasoning": "<concise explanation>"
}}
"""

_RISK_EVAL_PROMPT = PromptTemplate(
    input_variables=[
        "policy_id",
        "age",
        "annual_income",
        "medical_history_flags",
        "claim_id",
        "claim_amount",
        "months_since_inception",
        "diagnosis_codes",
    ],
    template=_RISK_EVAL_TEMPLATE,
)

# ---------------------------------------------------------------------------
# Valid recommendation literals (guards against hallucinated values)
# ---------------------------------------------------------------------------
_VALID_RECOMMENDATIONS = {"Approve", "Escalate to Underwriter", "Reject"}


class InsuranceRiskEvaluator:
    """Evaluates life-insurance claims against policyholder profiles using
    IBM Granite via ibm-watsonx-ai and returns a structured RiskEvaluationReport.

    Required environment variables:
        WATSONX_API_KEY   – IBM Cloud API key
        WATSONX_URL       – watsonx.ai service URL
                           (e.g. https://us-south.ml.cloud.ibm.com)
        WATSONX_PROJECT_ID – watsonx.ai project ID
    """

    #: Granite model used for risk evaluation
    MODEL_ID: str = "ibm/granite-13b-instruct-v2"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        url: str | None = None,
        project_id: str | None = None,
        max_new_tokens: int = 512,
        temperature: float = 0.0,
    ) -> None:
        resolved_api_key = api_key or os.environ["WATSONX_API_KEY"]
        resolved_url = url or os.environ["WATSONX_URL"]
        resolved_project_id = project_id or os.environ["WATSONX_PROJECT_ID"]

        self._llm = WatsonxLLM(
            model_id=self.MODEL_ID,
            url=SecretStr(resolved_url),
            api_key=SecretStr(resolved_api_key),
            project_id=resolved_project_id,
            params={
                GenParams.MAX_NEW_TOKENS: max_new_tokens,
                GenParams.TEMPERATURE: temperature,
                # Deterministic output is critical for structured JSON parsing
                GenParams.DECODING_METHOD: "greedy",
            },
        )

        self._chain = _RISK_EVAL_PROMPT | self._llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        claim: ClaimSubmission,
        profile: PolicyholderProfile,
    ) -> RiskEvaluationReport:
        """Run a risk evaluation for *claim* against *profile*.

        Returns:
            A fully populated :class:`RiskEvaluationReport`.

        Raises:
            ValueError: If the LLM returns a response that cannot be parsed
                        into a valid report structure.
            RuntimeError: If the ibm-watsonx-ai API call itself fails.
        """
        prompt_values: dict[str, Any] = {
            "policy_id": profile.policy_id,
            "age": profile.age,
            "annual_income": profile.annual_income,
            "medical_history_flags": ", ".join(profile.medical_history_flags) or "None",
            "claim_id": claim.claim_id,
            "claim_amount": claim.claim_amount,
            "months_since_inception": claim.months_since_inception,
            "diagnosis_codes": ", ".join(claim.diagnosis_codes) or "None",
        }

        logger.info(
            "Sending claim %s (policy %s) to Granite for risk evaluation.",
            claim.claim_id,
            claim.policy_id,
        )

        try:
            raw_response: str = self._chain.invoke(prompt_values)
        except Exception as exc:
            raise RuntimeError(
                f"ibm-watsonx-ai API call failed for claim '{claim.claim_id}': {exc}"
            ) from exc

        return self._parse_response(raw_response, claim.claim_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str, claim_id: str) -> RiskEvaluationReport:
        """Parse the raw LLM string into a :class:`RiskEvaluationReport`."""
        cleaned = raw.strip()

        try:
            payload: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(
                "Granite returned non-JSON output for claim %s:\n%s", claim_id, cleaned
            )
            raise ValueError(
                f"LLM response for claim '{claim_id}' is not valid JSON: {exc}"
            ) from exc

        # --- field-level validation ----------------------------------------
        risk_score = payload.get("risk_score")
        if not isinstance(risk_score, (int, float)) or not (0.0 <= risk_score <= 1.0):
            raise ValueError(
                f"'risk_score' must be a float in [0.0, 1.0]; got {risk_score!r}"
            )

        recommendation = payload.get("recommendation", "")
        if recommendation not in _VALID_RECOMMENDATIONS:
            raise ValueError(
                f"'recommendation' must be one of {_VALID_RECOMMENDATIONS}; "
                f"got {recommendation!r}"
            )

        anomalies = payload.get("flagged_anomalies", [])
        if not isinstance(anomalies, list):
            raise ValueError(
                f"'flagged_anomalies' must be a list; got {type(anomalies).__name__}"
            )

        ai_reasoning = payload.get("ai_reasoning", "")
        if not isinstance(ai_reasoning, str):
            raise ValueError(
                f"'ai_reasoning' must be a string; got {type(ai_reasoning).__name__}"
            )

        logger.info(
            "Claim %s evaluated — risk_score=%.2f, recommendation=%s",
            claim_id,
            risk_score,
            recommendation,
        )

        return RiskEvaluationReport(
            claim_id=claim_id,
            risk_score=float(risk_score),
            flagged_anomalies=[str(a) for a in anomalies],
            recommendation=recommendation,
            ai_reasoning=ai_reasoning,
        )
