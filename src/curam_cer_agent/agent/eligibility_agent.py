"""
LangChain eligibility determination agent.

Connects to MCP tools (or uses direct tool bindings), uses GPT-4o/Claude,
and returns structured EligibilityDecision objects. Supports assess,
batch_assess, and parallel_run for validation.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from curam_cer_agent.agent.prompts import SYSTEM_PROMPT
from curam_cer_agent.mcp.tools import (
    assess_household_eligibility,
    check_period_eligibility,
    explain_eligibility_decision,
    get_applicable_programs,
    validate_evidence_completeness,
)
from curam_cer_agent.models.decision import (
    DecisionStatus,
    EligibilityDecision,
    RuleExecution,
)
from curam_cer_agent.ontology.reasoner import OntologyReasoner
from curam_cer_agent.utils.config import (
    get_llm_model,
    get_llm_provider,
)

logger = logging.getLogger(__name__)


class CaseData(BaseModel):
    """Input case data for eligibility assessment."""

    household_id: str
    program_code: str = "SNAP"
    household_size: int = Field(..., ge=1)
    gross_monthly_income: float = Field(..., ge=0)
    state: str = Field(..., min_length=2, max_length=2)
    identity_verified: bool = True
    assessment_date: str = "2026-02-23"


class ComparisonResult(BaseModel):
    """Result of parallel run: agent vs direct evaluation."""

    case_id: str
    agent_status: str
    direct_status: str
    agree: bool
    agent_decision: dict
    direct_decision: dict
    match_explanation: str


def _household_dict(c: CaseData) -> dict:
    """Convert CaseData to household dict for tools."""
    return {
        "household_size": c.household_size,
        "gross_monthly_income": c.gross_monthly_income,
        "state": c.state.upper(),
        "identity_verified": c.identity_verified,
    }


def _tools_as_langchain() -> list:
    """Wrap MCP tools as LangChain StructuredTools for agent use."""
    return [
        StructuredTool.from_function(
            func=lambda **kw: assess_household_eligibility(**kw),
            name="assess_household_eligibility",
            description="Assess household eligibility for a program. Input: household_id, program_code, assessment_date, household dict (size, gross_monthly_income, state, identity_verified). Returns full decision with audit trail.",
            args_schema=None,
        ),
        StructuredTool.from_function(
            func=lambda **kw: check_period_eligibility(**kw),
            name="check_period_eligibility",
            description="Check period eligibility. Input: household_id, program_code, period_start, period_end, household dict.",
            args_schema=None,
        ),
        StructuredTool.from_function(
            func=lambda **kw: explain_eligibility_decision(**kw),
            name="explain_eligibility_decision",
            description="Explain a decision. Input: decision_id, audience (case_worker|applicant|auditor), decision_data.",
            args_schema=None,
        ),
        StructuredTool.from_function(
            func=lambda **kw: get_applicable_programs(**kw),
            name="get_applicable_programs",
            description="Get programs household may qualify for. Input: state, household_size, monthly_income.",
            args_schema=None,
        ),
        StructuredTool.from_function(
            func=lambda **kw: validate_evidence_completeness(**kw),
            name="validate_evidence_completeness",
            description="Validate evidence completeness. Input: household_id, program_code, evidence_submitted.",
            args_schema=None,
        ),
    ]


def _get_llm():
    """Create LLM instance from config."""
    provider = get_llm_provider().lower()
    model = get_llm_model()
    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model, temperature=0)
        except ImportError:
            logger.warning("langchain-anthropic not installed, falling back to OpenAI")
    return ChatOpenAI(model=model, temperature=0)


class EligibilityAgent:
    """
    LangChain agent for eligibility determination.

    Uses ontology tools only (never hallucinates). Returns EligibilityDecision.
    Supports batch_assess and parallel_run for validation.
    """

    def __init__(
        self,
        llm=None,
        tools: Optional[list] = None,
    ):
        # LLM is only needed for assess_with_llm(); assess() uses tools directly
        self._llm = llm
        self.tools = tools or _tools_as_langchain()
        self.reasoner = OntologyReasoner()

    @property
    def llm(self):
        """Lazy-load LLM only when needed (e.g., for assess_with_llm)."""
        if self._llm is None:
            self._llm = _get_llm()
        return self._llm

    def assess(self, case: CaseData) -> EligibilityDecision:
        """
        Assess a single case. Uses direct tool call (no LLM for determination).
        The ontology tools perform the actual logic; we use them directly
        for reliability and to avoid hallucination.
        """
        h = _household_dict(case)
        result = assess_household_eligibility(
            household_id=case.household_id,
            program_code=case.program_code,
            assessment_date=case.assessment_date,
            household=h,
        )
        rule_execs = []
        for r in result.get("rule_executions", []):
            rule_execs.append(
                RuleExecution(
                    rule_id=r.get("rule_id", ""),
                    rule_result=r.get("rule_result", False),
                    rule_reason=r.get("rule_reason", ""),
                    timestamp=(
                        datetime.fromisoformat(r["timestamp"])
                        if r.get("timestamp") else None
                    ),
                    threshold_used=r.get("threshold_used"),
                    actual_value=r.get("actual_value"),
                )
            )
        return EligibilityDecision(
            decision_id=result["decision_id"],
            status=DecisionStatus(result["status"]),
            program_code=result["program_code"],
            household_id=result["household_id"],
            period_start=result.get("period_start"),
            period_end=result.get("period_end"),
            rule_executions=rule_execs,
            explanation=result.get("explanation", ""),
            requires_human_review=result.get("requires_human_review", False),
        )

    def assess_with_llm(self, case: CaseData) -> EligibilityDecision:
        """
        Assess via LLM agent (uses tools). For cases where we want
        natural language interaction. Still constrains to ontology tools.
        """
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.messages import HumanMessage, SystemMessage

        agent = create_tool_calling_agent(self.llm, self.tools, [
            SystemMessage(content=SYSTEM_PROMPT),
        ])
        executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        h = _household_dict(case)
        prompt = (
            f"Assess eligibility for household {case.household_id} for program {case.program_code}. "
            f"household_id={case.household_id}, program_code={case.program_code}, "
            f"assessment_date={case.assessment_date}, household={h}. "
            "Call assess_household_eligibility and return the decision."
        )
        out = executor.invoke({"messages": [HumanMessage(content=prompt)]})
        # Parse last message / tool output into EligibilityDecision
        # For robustness, we fall back to direct assess if parsing fails
        try:
            last = out.get("messages", [])[-1]
            content = getattr(last, "content", "")
            if isinstance(content, str) and "ELIGIBLE" in content:
                # Could parse from content; for now use direct
                return self.assess(case)
        except Exception:
            pass
        return self.assess(case)

    def batch_assess(self, cases: list[CaseData]) -> list[EligibilityDecision]:
        """Process multiple cases and return list of decisions."""
        return [self.assess(c) for c in cases]

    def parallel_run(self, case: CaseData) -> ComparisonResult:
        """
        Run the same case through (a) ontology-based agent and (b) direct
        rule evaluation. Returns ComparisonResult showing whether they agree.
        Used to validate the agent against known-good rule execution.
        """
        agent_decision = self.assess(case)
        direct_decision = self.reasoner.assess_eligibility(
            household_id=case.household_id,
            program_code=case.program_code,
            household_size=case.household_size,
            gross_monthly_income=case.gross_monthly_income,
            state=case.state.upper(),
            identity_verified=case.identity_verified,
            assessment_date=case.assessment_date,
        )
        agree = agent_decision.status == direct_decision.status
        return ComparisonResult(
            case_id=case.household_id,
            agent_status=agent_decision.status.value,
            direct_status=direct_decision.status.value,
            agree=agree,
            agent_decision=agent_decision.to_dict(),
            direct_decision=direct_decision.to_dict(),
            match_explanation=(
                "Agent and direct evaluation agree."
                if agree
                else f"Discrepancy: agent={agent_decision.status.value}, direct={direct_decision.status.value}"
            ),
        )
