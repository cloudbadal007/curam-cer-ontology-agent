"""
MCP tool implementations for eligibility determination.

Each tool validates inputs with Pydantic, calls the ontology reasoner,
and returns structured dicts. All invocations are logged for audit.
"""

import logging
import time
from typing import Any

from pydantic import BaseModel, Field

from curam_cer_agent.ontology.reasoner import OntologyReasoner
from curam_cer_agent.utils.audit import log_tool_invocation

logger = logging.getLogger(__name__)

# Required evidence types per program (from ontology/program model)
REQUIRED_EVIDENCE = {
    "SNAP": ["identity", "residency", "income"],
    "MEDICAID": ["identity", "residency", "income"],
}


class AssessHouseholdInput(BaseModel):
    """Input for assess_household_eligibility."""

    household_id: str = Field(..., description="Unique household identifier")
    program_code: str = Field(..., description="Program code (e.g., SNAP, MEDICAID)")
    assessment_date: str = Field(
        ...,
        description="Assessment date in ISO format (YYYY-MM-DD)",
    )
    household: dict = Field(
        ...,
        description="Household data: size, gross_monthly_income, state, identity_verified",
    )


class CheckPeriodInput(BaseModel):
    """Input for check_period_eligibility."""

    household_id: str
    program_code: str
    period_start: str = Field(..., description="Period start (ISO date)")
    period_end: str = Field(..., description="Period end (ISO date)")
    household: dict


class ExplainDecisionInput(BaseModel):
    """Input for explain_eligibility_decision."""

    decision_id: str
    audience: str = Field(
        ...,
        description="case_worker | applicant | auditor",
    )
    decision_data: dict = Field(
        default_factory=dict,
        description="Full decision object (if decision_id lookup not available)",
    )


class GetProgramsInput(BaseModel):
    """Input for get_applicable_programs."""

    state: str = Field(..., min_length=2, max_length=2)
    household_size: int = Field(..., ge=1, le=20)
    monthly_income: float = Field(..., ge=0)


class ValidateEvidenceInput(BaseModel):
    """Input for validate_evidence_completeness."""

    household_id: str
    program_code: str
    evidence_submitted: dict = Field(
        default_factory=dict,
        description="Dict of evidence type -> bool or list of records",
    )


def _extract_household_params(household: dict) -> tuple[int, float, str, bool]:
    """Extract and validate household parameters from dict."""
    size = int(household.get("household_size", household.get("size", 1)))
    income = float(
        household.get("gross_monthly_income", household.get("monthly_income", 0))
    )
    state = str(household.get("state", "")).upper()[:2]
    identity_verified = bool(household.get("identity_verified", False))
    return size, income, state, identity_verified


def assess_household_eligibility(
    household_id: str,
    program_code: str,
    assessment_date: str,
    household: dict,
) -> dict[str, Any]:
    """
    Assess household eligibility for a program.

    Loads household facts into working RDF graph, runs SPARQL eligibility
    query against ontology, returns structured decision with full audit trail.
    """
    start = time.perf_counter()
    try:
        size, income, state, identity_verified = _extract_household_params(household)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid household data: {e}") from e

    reasoner = OntologyReasoner()
    decision = reasoner.assess_eligibility(
        household_id=household_id,
        program_code=program_code.upper(),
        household_size=size,
        gross_monthly_income=income,
        state=state,
        identity_verified=identity_verified,
        assessment_date=assessment_date,
    )
    result = decision.to_dict()
    duration = (time.perf_counter() - start) * 1000
    log_tool_invocation("assess_household_eligibility", {"household_id": household_id}, result, duration)
    return result


def check_period_eligibility(
    household_id: str,
    program_code: str,
    period_start: str,
    period_end: str,
    household: dict,
) -> list[dict]:
    """
    Check eligibility for a date range (period-by-period).

    Replicates Cúram's week-by-week period eligibility. Each period is
    assessed independently based on evidence active during that period.
    """
    start = time.perf_counter()
    try:
        size, income, state, identity_verified = _extract_household_params(household)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid household data: {e}") from e

    reasoner = OntologyReasoner()
    periods = reasoner.assess_period_eligibility(
        household_id=household_id,
        program_code=program_code.upper(),
        period_start=period_start,
        period_end=period_end,
        household_size=size,
        gross_monthly_income=income,
        state=state,
        identity_verified=identity_verified,
    )
    result = {"periods": periods}
    duration = (time.perf_counter() - start) * 1000
    log_tool_invocation("check_period_eligibility", {"household_id": household_id}, result, duration)
    return periods


def explain_eligibility_decision(
    decision_id: str,
    audience: str,
    decision_data: dict | None = None,
) -> dict[str, Any]:
    """
    Generate plain English explanation of an eligibility decision.

    Tailored by audience:
    - case_worker: Technical summary with rule chain and threshold values
    - applicant: Plain English without jargon, actionable next steps
    - auditor: Full rule execution log with timestamps and data values
    """
    start = time.perf_counter()
    data = decision_data or {}
    if not data and decision_id:
        # In a real system, would lookup by decision_id; for now use provided data
        return {
            "decision_id": decision_id,
            "audience": audience,
            "explanation": "Decision data not provided. Pass decision_data for explanation.",
            "error": "decision_data required when no persistence",
        }

    status = data.get("status", "UNKNOWN")
    explanation = data.get("explanation", "")
    rule_executions = data.get("rule_executions", [])

    if audience == "case_worker":
        lines = [
            f"**Decision**: {status}",
            f"**Summary**: {explanation}",
            "**Rule chain:**",
        ]
        for r in rule_executions:
            lines.append(f"  - {r.get('rule_id')}: {'PASS' if r.get('rule_result') else 'FAIL'} — {r.get('rule_reason', '')}")
        out = {"explanation": "\n".join(lines), "audience": audience}
    elif audience == "applicant":
        if status == "ELIGIBLE":
            out = {
                "explanation": (
                    "Your application appears to meet the eligibility criteria. "
                    "You will receive a formal notice by mail with next steps."
                ),
                "audience": audience,
                "next_steps": ["Wait for formal notice", "Contact your local office if you have questions"],
            }
        elif status == "INELIGIBLE":
            out = {
                "explanation": "Based on the information provided, your household does not currently meet the income guidelines for this program.",
                "audience": audience,
                "next_steps": ["You may reapply if your circumstances change", "Contact your local office to discuss other assistance options"],
            }
        else:
            out = {
                "explanation": "We need to verify your identity before we can complete your application. Please submit the requested documents.",
                "audience": audience,
                "next_steps": ["Submit a valid ID document", "Check your mail for a request letter"],
            }
    else:  # auditor
        lines = [
            f"Decision ID: {decision_id}",
            f"Status: {status}",
            f"Explanation: {explanation}",
            "**Rule execution log:**",
        ]
        for r in rule_executions:
            ts = r.get("timestamp", "N/A")
            th = r.get("threshold_used")
            av = r.get("actual_value")
            detail = f" (threshold={th}, actual={av})" if th is not None and av is not None else ""
            lines.append(f"  [{ts}] {r.get('rule_id')}: {r.get('rule_result')} — {r.get('rule_reason', '')}{detail}")
        out = {"explanation": "\n".join(lines), "audience": audience, "full_log": True}

    out["decision_id"] = decision_id
    duration = (time.perf_counter() - start) * 1000
    log_tool_invocation("explain_eligibility_decision", {"decision_id": decision_id}, out, duration)
    return out


def get_applicable_programs(
    state: str,
    household_size: int,
    monthly_income: float,
) -> list[dict]:
    """
    Get programs the household may qualify for.

    Queries ontology for programs administered in the state where
    income threshold could potentially be met.
    """
    start = time.perf_counter()
    state = state.upper()[:2]
    programs = []

    # SNAP: 130% FPL limits (FY2026)
    snap_limits = {
        1: 1696, 2: 2292, 3: 2888, 4: 3483,
        5: 4079, 6: 4675, 7: 5271, 8: 5867,
    }
    size_key = min(household_size, 8)
    snap_limit = snap_limits.get(size_key)
    if snap_limit and monthly_income <= snap_limit:
        programs.append({
            "program_code": "SNAP",
            "program_name": "Supplemental Nutrition Assistance Program",
            "potentially_eligible": True,
            "income_limit_used": snap_limit,
            "administered_in_state": "all",
        })

    # Medicaid stub — always list as potential (state-specific rules)
    programs.append({
        "program_code": "MEDICAID",
        "program_name": "Medicaid",
        "potentially_eligible": True,
        "income_limit_used": None,
        "administered_in_state": state,
        "note": "State-specific rules apply; contact state agency",
    })

    result = {"programs": programs, "state": state}
    duration = (time.perf_counter() - start) * 1000
    log_tool_invocation("get_applicable_programs", {"state": state}, result, duration)
    return programs


def validate_evidence_completeness(
    household_id: str,
    program_code: str,
    evidence_submitted: dict | None = None,
) -> dict[str, Any]:
    """
    Check which evidence types are missing before a determination can be made.

    Returns list of missing evidence types required by the program.
    """
    start = time.perf_counter()
    evidence_submitted = evidence_submitted or {}
    required = REQUIRED_EVIDENCE.get(program_code.upper(), ["identity", "residency", "income"])
    missing = []
    for ev_type in required:
        val = evidence_submitted.get(ev_type)
        if val is None or val is False or (isinstance(val, list) and len(val) == 0):
            missing.append(ev_type)
    result = {
        "household_id": household_id,
        "program_code": program_code,
        "missing_evidence": missing,
        "required_evidence": required,
        "complete": len(missing) == 0,
    }
    duration = (time.perf_counter() - start) * 1000
    log_tool_invocation("validate_evidence_completeness", {"household_id": household_id}, result, duration)
    return result
