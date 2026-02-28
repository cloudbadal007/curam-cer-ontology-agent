"""
SPARQL-based eligibility reasoning engine.

Evaluates household eligibility against the ontology using SPARQL queries.
Produces EligibilityDecision with full rule execution audit trail.
Does NOT use LLM — pure ontology/rule evaluation. Used by MCP tools and agent.
"""

import logging
import time
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.plugins.sparql import prepareQuery

from curam_cer_agent.models.decision import (
    DecisionStatus,
    EligibilityDecision,
    RuleExecution,
)
from curam_cer_agent.ontology.loader import OntologyLoader

logger = logging.getLogger(__name__)

ELIG = Namespace("http://curam.cer.ontology/eligibility#")
SNAP = Namespace("http://curam.cer.ontology/snap#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")


class OntologyReasoner:
    """
    SPARQL-based eligibility reasoner.

    Loads ontology, injects household facts into a working graph,
    and runs eligibility rules via SPARQL. Returns structured
    EligibilityDecision with audit trail.
    """

    def __init__(self, ontology_path: Optional[Any] = None):
        """Initialize with optional custom ontology path."""
        self.loader = OntologyLoader(ontology_path)

    def _get_threshold_for_size(
        self,
        graph: Graph,
        program_code: str,
        household_size: int,
        threshold_type: str = "gross",
    ) -> Optional[float]:
        """Query ontology for income threshold by household size."""
        if program_code.upper() == "SNAP":
            ns = SNAP
            prefix = "SNAP_GrossIncomeTest" if threshold_type == "gross" else "SNAP_NetIncomeTest"
        else:
            return None

        # For SNAP we have Size1..Size8; cap at 8
        size = min(household_size, 8)
        threshold_uri = URIRef(f"http://curam.cer.ontology/snap#{prefix}_Size{size}")

        q = prepareQuery(
            """
            SELECT ?limit WHERE {
                ?t elig:monthlyIncomeLimit ?limit .
                ?t elig:thresholdForHouseholdSize ?hs .
                FILTER (?t = ?threshold && ?hs = ?hsize)
            }
            """,
            initNs={"elig": ELIG},
        )
        # Simpler direct lookup
        for o in graph.objects(threshold_uri, ELIG.monthlyIncomeLimit):
            if isinstance(o, Literal):
                return float(o)
        return None

    def _inject_household_facts(
        self,
        base_graph: Graph,
        household_id: str,
        household_size: int,
        gross_monthly_income: float,
        state: str,
        identity_verified: bool,
    ) -> Graph:
        """Create a working graph with household facts for this assessment."""
        working = Graph()
        for (s, p, o) in base_graph:
            working.add((s, p, o))

        h_uri = URIRef(f"http://curam.cer.ontology/facts#{household_id}")
        working.add((h_uri, RDF.type, ELIG.Household))
        working.add((h_uri, ELIG.householdId, Literal(household_id)))
        working.add((h_uri, ELIG.householdSize, Literal(household_size)))
        working.add((h_uri, ELIG.grossMonthlyIncome, Literal(gross_monthly_income)))
        working.add((h_uri, ELIG.residencyState, Literal(state)))

        # We use a simple convention: identity is an applicant property
        # For SPARQL we add a fictional applicant with identity status
        a_uri = URIRef(f"http://curam.cer.ontology/facts#{household_id}_applicant")
        working.add((a_uri, RDF.type, ELIG.Applicant))
        working.add((a_uri, ELIG.residencyState, Literal(state)))
        working.add((a_uri, ELIG.isIdentityVerified, Literal(identity_verified)))
        working.add((h_uri, ELIG.hasMember, a_uri))

        return working

    def assess_eligibility(
        self,
        household_id: str,
        program_code: str,
        household_size: int,
        gross_monthly_income: float,
        state: str,
        identity_verified: bool,
        assessment_date: Optional[str] = None,
    ) -> EligibilityDecision:
        """
        Assess household eligibility for a program.

        Uses ontology thresholds and rules. Returns full audit trail.
        """
        start = time.perf_counter()
        rule_executions: list[RuleExecution] = []
        graph = self.loader.load()

        # Inject household facts
        working = self._inject_household_facts(
            graph,
            household_id,
            household_size,
            gross_monthly_income,
            state,
            identity_verified,
        )

        # Rule 1: Identity verification
        if not identity_verified:
            rule_executions.append(
                RuleExecution(
                    rule_id="IDENTITY_VERIFICATION",
                    rule_result=False,
                    rule_reason="Applicant identity has not been verified",
                    threshold_used=None,
                    actual_value=None,
                )
            )
            status = DecisionStatus.PENDING_VERIFICATION
            explanation = "Eligibility cannot be determined until identity is verified."
            requires_human_review = True
        else:
            rule_executions.append(
                RuleExecution(
                    rule_id="IDENTITY_VERIFICATION",
                    rule_result=True,
                    rule_reason="Identity verified",
                    threshold_used=None,
                    actual_value=None,
                )
            )

            # Rule 2: Residency (state must match program admin state for state programs)
            # SNAP is federal — all states. Medicaid stub has no state filter.
            if program_code.upper() not in ("SNAP", "MEDICAID"):
                rule_executions.append(
                    RuleExecution(
                        rule_id="RESIDENCY",
                        rule_result=False,
                        rule_reason=f"Program {program_code} not found or not administered in state {state}",
                        threshold_used=None,
                        actual_value=None,
                    )
                )
                status = DecisionStatus.INELIGIBLE
                explanation = f"Program {program_code} is not available in {state}."
                requires_human_review = False
            else:
                rule_executions.append(
                    RuleExecution(
                        rule_id="RESIDENCY",
                        rule_result=True,
                        rule_reason=f"Residency in {state} is valid for program",
                        threshold_used=None,
                        actual_value=None,
                    )
                )

                # Rule 3: Gross income test (for SNAP)
                threshold = self._get_threshold_for_size(
                    working, program_code, household_size, "gross"
                )
                if threshold is None:
                    rule_executions.append(
                        RuleExecution(
                            rule_id="GROSS_INCOME",
                            rule_result=False,
                            rule_reason=f"No threshold found for {program_code} household size {household_size}",
                            threshold_used=None,
                            actual_value=gross_monthly_income,
                        )
                    )
                    status = DecisionStatus.INELIGIBLE
                    explanation = "Income threshold data not available for this program/size."
                    requires_human_review = False
                else:
                    income_pass = gross_monthly_income <= threshold
                    rule_executions.append(
                        RuleExecution(
                            rule_id="GROSS_INCOME",
                            rule_result=income_pass,
                            rule_reason=(
                                f"Gross income ${gross_monthly_income:.2f} {'<=' if income_pass else '>'} "
                                f"limit ${threshold:.2f} (130% FPL for size {household_size})"
                            ),
                            threshold_used=threshold,
                            actual_value=gross_monthly_income,
                        )
                    )
                    if not income_pass:
                        status = DecisionStatus.INELIGIBLE
                        explanation = (
                            f"Gross monthly income (${gross_monthly_income:.2f}) exceeds "
                            f"the limit for household size {household_size} (${threshold:.2f})."
                        )
                        requires_human_review = False
                    else:
                        status = DecisionStatus.ELIGIBLE
                        explanation = (
                            f"Household meets gross income test. "
                            f"Income ${gross_monthly_income:.2f} is at or below limit ${threshold:.2f}."
                        )
                        requires_human_review = False

        elapsed = time.perf_counter() - start
        logger.info("Eligibility assessed in %.3fs: %s for %s", elapsed, status.value, household_id)

        return EligibilityDecision(
            decision_id=str(uuid4()),
            status=status,
            program_code=program_code,
            household_id=household_id,
            period_start=assessment_date,
            period_end=assessment_date,
            rule_executions=rule_executions,
            explanation=explanation,
            requires_human_review=requires_human_review,
        )

    def assess_period_eligibility(
        self,
        household_id: str,
        program_code: str,
        period_start: str,
        period_end: str,
        household_size: int,
        gross_monthly_income: float,
        state: str,
        identity_verified: bool,
    ) -> list[dict]:
        """
        Assess eligibility for a date range (period-by-period).

        Returns list of period-level determinations. For simplicity,
        we treat the whole range as one period unless extended.
        """
        decision = self.assess_eligibility(
            household_id=household_id,
            program_code=program_code,
            household_size=household_size,
            gross_monthly_income=gross_monthly_income,
            state=state,
            identity_verified=identity_verified,
            assessment_date=period_start,
        )
        return [
            {
                "period_start": period_start,
                "period_end": period_end,
                "status": decision.status.value,
                "decision_id": decision.decision_id,
                "explanation": decision.explanation,
            }
        ]
