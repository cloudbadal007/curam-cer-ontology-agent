"""
Integration tests for EligibilityAgent.

Uses mocked or direct assessment (no LLM required for core tests).
"""

import json
from pathlib import Path

import pytest

from curam_cer_agent.agent.eligibility_agent import CaseData, EligibilityAgent


def test_agent_returns_structured_decision(case_eligible) -> None:
    """Arrange: eligible case. Act: agent.assess. Assert: EligibilityDecision."""
    agent = EligibilityAgent()
    decision = agent.assess(case_eligible)
    assert decision.status.value in ("ELIGIBLE", "INELIGIBLE", "PENDING_VERIFICATION")
    assert decision.program_code == "SNAP"
    assert decision.household_id == case_eligible.household_id


def test_agent_audit_trail_present(case_eligible) -> None:
    """Arrange: case. Act: assess. Assert: rule_executions not empty."""
    agent = EligibilityAgent()
    decision = agent.assess(case_eligible)
    assert len(decision.rule_executions) > 0


def test_agent_parallel_run_matches_direct_evaluation(case_eligible) -> None:
    """Arrange: case. Act: parallel_run. Assert: agent and direct agree."""
    agent = EligibilityAgent()
    result = agent.parallel_run(case_eligible)
    assert result.agree is True
    assert result.agent_status == result.direct_status


def test_batch_assess_10_cases() -> None:
    """Arrange: 10 cases from fixtures. Act: batch_assess. Assert: 10 decisions."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "sample_cases.json"
    with open(fixtures_path, encoding="utf-8") as f:
        cases_raw = json.load(f)[:10]
    cases = [
        CaseData(
            household_id=c["household_id"],
            program_code="SNAP",
            household_size=c["household_size"],
            gross_monthly_income=c["gross_monthly_income"],
            state=c["state"],
            identity_verified=c["identity_verified"],
            assessment_date="2026-02-23",
        )
        for c in cases_raw
    ]
    agent = EligibilityAgent()
    decisions = agent.batch_assess(cases)
    assert len(decisions) == 10
    for d in decisions:
        assert d.decision_id
        assert d.status.value in ("ELIGIBLE", "INELIGIBLE", "PENDING_VERIFICATION")
