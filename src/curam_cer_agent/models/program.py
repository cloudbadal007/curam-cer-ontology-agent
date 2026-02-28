"""
Pydantic models for benefit programs and policy thresholds.

These models represent government programs and their legislated
limits (e.g., 130% FPL for SNAP). Maps to OWL Program and PolicyThreshold.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PolicyThreshold(BaseModel):
    """
    A legislated limit for a program (e.g., 130% FPL for SNAP gross income).

    Maps to OWL class PolicyThreshold.
    """

    threshold_id: str = Field(..., description="Unique threshold identifier")
    threshold_type: str = Field(
        ...,
        description="gross_income | net_income | asset | resource",
    )
    threshold_percent_fpl: Optional[float] = Field(
        default=None, description="Percentage of Federal Poverty Level (e.g., 130)"
    )
    household_size: int = Field(
        ...,
        ge=1,
        le=10,
        description="Household size this threshold applies to",
    )
    monthly_limit: Optional[float] = Field(
        default=None, description="Monthly income limit in USD"
    )
    effective_date: Optional[date] = Field(
        default=None, description="When this threshold became effective"
    )
    admin_state: Optional[str] = Field(
        default=None, description="State code if state-specific"
    )


class EligibilityPeriod(BaseModel):
    """
    A specific week or month for which eligibility is assessed.

    Maps to OWL class EligibilityPeriod. Cúram uses period-based
    eligibility (week-by-week or month-by-month).
    """

    period_id: str = Field(..., description="Unique period identifier")
    period_start: date = Field(..., description="Start date of the period")
    period_end: date = Field(..., description="End date of the period")
    period_type: str = Field(
        default="monthly",
        description="weekly | biweekly | monthly",
    )


class Program(BaseModel):
    """
    A government benefit program (e.g., SNAP, Medicaid).

    Maps to OWL class Program.
    """

    program_code: str = Field(..., description="Unique program code (e.g., SNAP)")
    program_name: str = Field(..., description="Human-readable program name")
    administered_in_states: list[str] = Field(
        default_factory=list,
        description="State codes where program is administered (empty = federal)",
    )
    thresholds: list[PolicyThreshold] = Field(
        default_factory=list,
        description="Policy thresholds for this program",
    )
    required_evidence_types: list[str] = Field(
        default_factory=lambda: ["identity", "residency", "income"],
        description="Evidence types required before determination",
    )
    is_federal: bool = Field(
        default=True,
        description="True if federal program, false if state-only",
    )
