"""
Pydantic models for household, applicant, and evidence data.

These models represent the input data structure for eligibility assessment,
aligning with the OWL ontology concepts: Applicant, Household, HouseholdMember,
and EvidenceRecord hierarchies.
"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Type of evidence submitted by an applicant."""

    INCOME = "income"
    RESIDENCY = "residency"
    IDENTITY = "identity"


class EvidenceRecord(BaseModel):
    """
    Base model for evidence submitted by an applicant.

    Maps to the OWL class EvidenceRecord in eligibility_core ontology.
    """

    record_id: str = Field(..., description="Unique identifier for the evidence record")
    submitted_date: Optional[date] = Field(
        default=None, description="Date evidence was submitted"
    )
    effective_start: Optional[date] = Field(
        default=None, description="Start of period this evidence covers"
    )
    effective_end: Optional[date] = Field(
        default=None, description="End of period this evidence covers"
    )
    is_verified: bool = Field(default=False, description="Whether evidence has been verified")


class IncomeEvidence(EvidenceRecord):
    """
    Evidence of income (pay stubs, tax returns, etc.).

    Subclass of EvidenceRecord in the ontology.
    """

    gross_monthly_amount: Optional[float] = Field(
        default=None, description="Gross monthly income amount"
    )
    income_source: Optional[str] = Field(
        default=None, description="Source of income (e.g., employment, self-employment)"
    )
    is_countable: bool = Field(default=True, description="Whether income counts toward limits")


class ResidencyEvidence(EvidenceRecord):
    """
    Evidence of residency (utility bill, lease, etc.).

    Subclass of EvidenceRecord in the ontology.
    """

    address: Optional[str] = Field(default=None, description="Residential address")
    state: Optional[str] = Field(default=None, description="State of residence (2-letter code)")
    county: Optional[str] = Field(default=None, description="County of residence")


class IdentityEvidence(EvidenceRecord):
    """
    Evidence of identity (ID, birth certificate, etc.).

    Subclass of EvidenceRecord in the ontology.
    """

    document_type: Optional[str] = Field(
        default=None, description="Type of ID document (e.g., driver license, passport)"
    )
    document_number: Optional[str] = Field(
        default=None, description="Last 4 of document number for audit"
    )
    verification_status: str = Field(
        default="pending",
        description="pending | verified | rejected",
    )


class HouseholdMember(BaseModel):
    """
    An individual member of a household.

    Maps to OWL class HouseholdMember.
    """

    member_id: str = Field(..., description="Unique identifier for the member")
    role: str = Field(
        default="applicant",
        description="Role: applicant, spouse, dependent, etc.",
    )
    is_primary_applicant: bool = Field(
        default=False, description="Whether this member is the primary applicant"
    )
    date_of_birth: Optional[date] = Field(default=None)
    ssn_last_four: Optional[str] = Field(default=None, description="Last 4 of SSN for matching")


class Applicant(BaseModel):
    """
    An individual applying for benefits.

    Maps to OWL class Applicant. Contains residency, identity status,
    and program application details.
    """

    applicant_id: str = Field(..., description="Unique identifier for the applicant")
    residency_state: str = Field(
        ...,
        description="State of residence (2-letter code, e.g., CA, NY)",
        min_length=2,
        max_length=2,
    )
    is_identity_verified: bool = Field(
        default=False, description="Whether identity has been verified"
    )
    evidence: list[EvidenceRecord] = Field(
        default_factory=list, description="Evidence submitted by this applicant"
    )
    applies_for_programs: list[str] = Field(
        default_factory=list, description="Program codes this applicant is applying for"
    )
    household_member: Optional[HouseholdMember] = Field(
        default=None, description="Household member details if applicable"
    )


class Household(BaseModel):
    """
    The unit of assessment for eligibility.

    Contains household size, gross monthly income, members, and applicants.
    Maps to OWL class Household.
    """

    household_id: str = Field(..., description="Unique identifier for the household")
    household_size: int = Field(
        ...,
        ge=1,
        le=20,
        description="Number of people in the household",
    )
    gross_monthly_income: float = Field(
        ...,
        ge=0,
        description="Total gross monthly income in USD",
    )
    state: str = Field(
        ...,
        description="State where household resides (2-letter code)",
        min_length=2,
        max_length=2,
    )
    members: list[HouseholdMember] = Field(
        default_factory=list, description="Household members"
    )
    applicants: list[Applicant] = Field(
        default_factory=list, description="Applicants in this household"
    )
    assessment_date: Optional[date] = Field(
        default=None, description="Date for which eligibility is assessed"
    )

    def to_assessment_dict(self) -> dict:
        """
        Convert to dict suitable for MCP tool input and ontology queries.

        Returns a flat structure with key eligibility attributes.
        """
        # Use primary applicant's identity status if present
        identity_verified = False
        if self.applicants:
            identity_verified = any(
                a.is_identity_verified for a in self.applicants
            )
        return {
            "household_id": self.household_id,
            "household_size": self.household_size,
            "gross_monthly_income": self.gross_monthly_income,
            "state": self.state,
            "identity_verified": identity_verified,
        }
