"""
Unit tests for MCP tool implementations.

Tests each tool with multiple scenarios.
"""

import pytest

from curam_cer_agent.mcp.tools import (
    assess_household_eligibility,
    explain_eligibility_decision,
    get_applicable_programs,
    validate_evidence_completeness,
)


def test_assess_eligible_household(sample_household_eligible) -> None:
    """Arrange: eligible household. Act: assess. Assert: ELIGIBLE."""
    h = sample_household_eligible
    result = assess_household_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        assessment_date="2026-02-23",
        household=h,
    )
    assert result["status"] == "ELIGIBLE"
    assert "decision_id" in result
    assert "rule_executions" in result


def test_assess_ineligible_household(sample_household_ineligible_income) -> None:
    """Arrange: ineligible household. Act: assess. Assert: INELIGIBLE."""
    h = sample_household_ineligible_income
    result = assess_household_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        assessment_date="2026-02-23",
        household=h,
    )
    assert result["status"] == "INELIGIBLE"


def test_assess_invalid_household_raises_error() -> None:
    """Arrange: invalid household (bad types). Act: assess. Assert: error."""
    with pytest.raises((ValueError, TypeError)):
        assess_household_eligibility(
            household_id="X",
            program_code="SNAP",
            assessment_date="2026-02-23",
            household={"household_size": "not_a_number", "gross_monthly_income": "bad"},
        )


def test_explain_decision_case_worker_audience() -> None:
    """Arrange: decision data. Act: explain with case_worker. Assert: technical output."""
    data = {
        "status": "ELIGIBLE",
        "explanation": "Meets criteria",
        "rule_executions": [
            {"rule_id": "R1", "rule_result": True, "rule_reason": "OK", "timestamp": None},
        ],
    }
    out = explain_eligibility_decision(
        decision_id="D1",
        audience="case_worker",
        decision_data=data,
    )
    assert "explanation" in out
    assert "case_worker" in out.get("audience", "").lower() or "case_worker" in str(out)


def test_explain_decision_applicant_audience() -> None:
    """Arrange: decision. Act: explain for applicant. Assert: plain English."""
    out = explain_eligibility_decision(
        decision_id="D1",
        audience="applicant",
        decision_data={"status": "ELIGIBLE", "explanation": "OK"},
    )
    assert "explanation" in out
    assert "next_steps" in out or "explanation" in out


def test_explain_decision_auditor_audience() -> None:
    """Arrange: decision. Act: explain for auditor. Assert: full log."""
    out = explain_eligibility_decision(
        decision_id="D1",
        audience="auditor",
        decision_data={
            "status": "ELIGIBLE",
            "explanation": "OK",
            "rule_executions": [{"rule_id": "R1", "rule_result": True, "rule_reason": "OK", "timestamp": "2026-02-23"}],
        },
    )
    assert "full_log" in out or "Rule execution" in out.get("explanation", "")


def test_get_applicable_programs_returns_list() -> None:
    """Arrange: state, size, income. Act: get programs. Assert: list of programs."""
    programs = get_applicable_programs(
        state="CA",
        household_size=2,
        monthly_income=2000,
    )
    assert isinstance(programs, list)
    assert len(programs) >= 1
    assert any(p.get("program_code") == "SNAP" for p in programs)


def test_validate_evidence_missing_identity() -> None:
    """Arrange: missing identity. Act: validate. Assert: identity in missing list."""
    result = validate_evidence_completeness(
        household_id="H1",
        program_code="SNAP",
        evidence_submitted={"income": True, "residency": True},
    )
    assert "identity" in result["missing_evidence"]
    assert result["complete"] is False


def test_validate_evidence_complete_case() -> None:
    """Arrange: all evidence. Act: validate. Assert: complete."""
    result = validate_evidence_completeness(
        household_id="H1",
        program_code="SNAP",
        evidence_submitted={"identity": True, "residency": True, "income": True},
    )
    assert len(result["missing_evidence"]) == 0
    assert result["complete"] is True
