"""
Unit tests for OntologyReasoner.

Verifies eligibility assessment logic against ontology.
"""

import time

import pytest

from curam_cer_agent.models.decision import DecisionStatus
from curam_cer_agent.ontology.reasoner import OntologyReasoner


def test_eligible_household_returns_eligible(reasoner, sample_household_eligible) -> None:
    """Arrange: eligible household. Act: assess. Assert: ELIGIBLE."""
    h = sample_household_eligible
    d = reasoner.assess_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
    )
    assert d.status == DecisionStatus.ELIGIBLE


def test_income_over_threshold_returns_ineligible(reasoner, sample_household_ineligible_income) -> None:
    """Arrange: income over limit. Act: assess. Assert: INELIGIBLE."""
    h = sample_household_ineligible_income
    d = reasoner.assess_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
    )
    assert d.status == DecisionStatus.INELIGIBLE


def test_unverified_identity_returns_pending(reasoner, sample_household_pending) -> None:
    """Arrange: identity not verified. Act: assess. Assert: PENDING_VERIFICATION."""
    h = sample_household_pending
    d = reasoner.assess_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
    )
    assert d.status == DecisionStatus.PENDING_VERIFICATION
    assert d.requires_human_review is True


def test_household_size_1_threshold_correct(reasoner) -> None:
    """Arrange: size 1, income at limit. Act: assess. Assert: ELIGIBLE."""
    d = reasoner.assess_eligibility(
        household_id="T1",
        program_code="SNAP",
        household_size=1,
        gross_monthly_income=1696,
        state="CA",
        identity_verified=True,
    )
    assert d.status == DecisionStatus.ELIGIBLE


def test_household_size_4_threshold_correct(reasoner) -> None:
    """Arrange: size 4, income at limit. Act: assess. Assert: ELIGIBLE."""
    d = reasoner.assess_eligibility(
        household_id="T4",
        program_code="SNAP",
        household_size=4,
        gross_monthly_income=3483,
        state="CA",
        identity_verified=True,
    )
    assert d.status == DecisionStatus.ELIGIBLE


def test_household_size_8_threshold_correct(reasoner) -> None:
    """Arrange: size 8, income at limit. Act: assess. Assert: ELIGIBLE."""
    d = reasoner.assess_eligibility(
        household_id="T8",
        program_code="SNAP",
        household_size=8,
        gross_monthly_income=5867,
        state="CA",
        identity_verified=True,
    )
    assert d.status == DecisionStatus.ELIGIBLE


def test_period_eligibility_single_month(reasoner, sample_household_eligible) -> None:
    """Arrange: eligible household. Act: period assess. Assert: one period result."""
    h = sample_household_eligible
    periods = reasoner.assess_period_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        period_start="2026-02-01",
        period_end="2026-02-28",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
    )
    assert len(periods) >= 1
    assert periods[0]["status"] == "ELIGIBLE"


def test_audit_trail_contains_all_rules(reasoner, sample_household_eligible) -> None:
    """Arrange: eligible household. Act: assess. Assert: rule_executions present."""
    h = sample_household_eligible
    d = reasoner.assess_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
    )
    rule_ids = [r.rule_id for r in d.rule_executions]
    assert "IDENTITY_VERIFICATION" in rule_ids
    assert "GROSS_INCOME" in rule_ids or "RESIDENCY" in rule_ids


def test_sparql_query_performance(reasoner, sample_household_eligible) -> None:
    """Arrange: household. Act: assess. Assert: completes under 500ms."""
    h = sample_household_eligible
    start = time.perf_counter()
    reasoner.assess_eligibility(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"Assessment took {elapsed*1000:.0f}ms (max 500ms)"
