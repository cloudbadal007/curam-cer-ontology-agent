"""
Shared pytest fixtures for curam-cer-ontology-agent.

Provides sample households, loaded ontology, and MCP server fixtures.
"""

import json
from pathlib import Path

import pytest

from curam_cer_agent.agent.eligibility_agent import CaseData
from curam_cer_agent.ontology.loader import OntologyLoader
from curam_cer_agent.ontology.reasoner import OntologyReasoner


@pytest.fixture
def sample_household_eligible() -> dict:
    """Household that clearly qualifies for SNAP (income below 130% FPL)."""
    return {
        "household_id": "HH-001",
        "household_size": 2,
        "gross_monthly_income": 1800.0,
        "state": "CA",
        "identity_verified": True,
    }


@pytest.fixture
def sample_household_ineligible_income() -> dict:
    """Household that fails the income test."""
    return {
        "household_id": "HH-002",
        "household_size": 2,
        "gross_monthly_income": 5000.0,
        "state": "CA",
        "identity_verified": True,
    }


@pytest.fixture
def sample_household_ineligible_residency() -> dict:
    """Household in wrong state (for state-specific programs)."""
    return {
        "household_id": "HH-003",
        "household_size": 2,
        "gross_monthly_income": 1500.0,
        "state": "XX",  # Invalid/unsupported
        "identity_verified": True,
    }


@pytest.fixture
def sample_household_pending() -> dict:
    """Household with identity not verified."""
    return {
        "household_id": "HH-004",
        "household_size": 2,
        "gross_monthly_income": 1500.0,
        "state": "CA",
        "identity_verified": False,
    }


@pytest.fixture
def snap_program() -> dict:
    """SNAP program info."""
    return {"program_code": "SNAP", "program_name": "Supplemental Nutrition Assistance Program"}


@pytest.fixture(scope="session")
def loaded_ontology():
    """Pre-loaded ontology graph (session-scoped for performance)."""
    loader = OntologyLoader()
    return loader.load()


@pytest.fixture
def reasoner():
    """OntologyReasoner instance."""
    return OntologyReasoner()


@pytest.fixture
def case_eligible(sample_household_eligible) -> CaseData:
    """CaseData for eligible household."""
    h = sample_household_eligible
    return CaseData(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
        assessment_date="2026-02-23",
    )


@pytest.fixture
def case_ineligible(sample_household_ineligible_income) -> CaseData:
    """CaseData for ineligible household."""
    h = sample_household_ineligible_income
    return CaseData(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
        assessment_date="2026-02-23",
    )


@pytest.fixture
def case_pending(sample_household_pending) -> CaseData:
    """CaseData for pending verification."""
    h = sample_household_pending
    return CaseData(
        household_id=h["household_id"],
        program_code="SNAP",
        household_size=h["household_size"],
        gross_monthly_income=h["gross_monthly_income"],
        state=h["state"],
        identity_verified=h["identity_verified"],
        assessment_date="2026-02-23",
    )
