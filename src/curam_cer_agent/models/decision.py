"""
Pydantic models for eligibility decisions and rule execution audit trails.

These models represent the output of eligibility assessment, including
the decision status, rule execution log, and audit metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    """Eligibility decision outcome. Maps to ontology decisionStatus values."""

    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class RuleExecution(BaseModel):
    """
    Audit record of a single rule being evaluated.

    Maps to OWL class RuleExecution. Used for full audit trail
    and explainability of eligibility determinations.
    """

    rule_id: str = Field(..., description="Unique rule identifier")
    rule_result: bool = Field(..., description="Whether the rule passed")
    rule_reason: str = Field(
        default="",
        description="Human-readable reason for the result",
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="When the rule was evaluated",
    )
    threshold_used: Optional[float] = Field(
        default=None, description="Threshold value used (e.g., income limit)"
    )
    actual_value: Optional[float] = Field(
        default=None, description="Actual value compared (e.g., household income)"
    )


class EligibilityDecision(BaseModel):
    """
    The output of an eligibility determination.

    Contains status, program, period, rule execution log, and
    human-readable explanation. Maps to OWL class EligibilityDecision.
    """

    decision_id: str = Field(..., description="Unique identifier for this decision")
    status: DecisionStatus = Field(..., description="Eligibility outcome")
    program_code: str = Field(..., description="Program for which eligibility was assessed")
    household_id: str = Field(..., description="Household that was assessed")
    period_start: Optional[str] = Field(
        default=None, description="Start of eligibility period (ISO date)"
    )
    period_end: Optional[str] = Field(
        default=None, description="End of eligibility period (ISO date)"
    )
    rule_executions: list[RuleExecution] = Field(
        default_factory=list,
        description="Audit trail of all rules evaluated",
    )
    explanation: str = Field(
        default="",
        description="Human-readable explanation of the decision",
    )
    requires_human_review: bool = Field(
        default=False,
        description="True if PENDING_VERIFICATION — must trigger human review",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the decision was made",
    )

    def to_dict(self) -> dict:
        """Convert to dict for API responses and MCP tool output."""
        return {
            "decision_id": self.decision_id,
            "status": self.status.value,
            "program_code": self.program_code,
            "household_id": self.household_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "rule_executions": [
                {
                    "rule_id": r.rule_id,
                    "rule_result": r.rule_result,
                    "rule_reason": r.rule_reason,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "threshold_used": r.threshold_used,
                    "actual_value": r.actual_value,
                }
                for r in self.rule_executions
            ],
            "explanation": self.explanation,
            "requires_human_review": self.requires_human_review,
            "created_at": self.created_at.isoformat(),
        }
