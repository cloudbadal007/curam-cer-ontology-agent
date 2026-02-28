"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from curam_cer_agent.models.decision import DecisionStatus, EligibilityDecision, RuleExecution
from curam_cer_agent.models.household import Applicant, Household, HouseholdMember


def test_household_to_assessment_dict() -> None:
    """Household.to_assessment_dict returns flat dict for tools."""
    h = Household(
        household_id="H1",
        household_size=2,
        gross_monthly_income=2000,
        state="CA",
    )
    d = h.to_assessment_dict()
    assert d["household_id"] == "H1"
    assert d["household_size"] == 2
    assert d["gross_monthly_income"] == 2000
    assert d["state"] == "CA"
    assert "identity_verified" in d


def test_eligibility_decision_to_dict() -> None:
    """EligibilityDecision.to_dict serializes correctly."""
    d = EligibilityDecision(
        decision_id="D1",
        status=DecisionStatus.ELIGIBLE,
        program_code="SNAP",
        household_id="H1",
        rule_executions=[],
    )
    out = d.to_dict()
    assert out["decision_id"] == "D1"
    assert out["status"] == "ELIGIBLE"
    assert out["program_code"] == "SNAP"


def test_applicant_validates_state_length() -> None:
    """Applicant requires 2-char state."""
    with pytest.raises(ValidationError):
        Applicant(applicant_id="A1", residency_state="CALIFORNIA")
    a = Applicant(applicant_id="A1", residency_state="CA")
    assert a.residency_state == "CA"
