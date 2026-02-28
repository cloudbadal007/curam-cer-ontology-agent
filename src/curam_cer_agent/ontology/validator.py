"""
Ontology integrity validation.

Performs checks on the loaded ontology to ensure required classes,
properties, and SNAP thresholds are present. Used for startup validation
and testing.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from rdflib import Graph, Namespace

from curam_cer_agent.ontology.loader import OntologyLoader

logger = logging.getLogger(__name__)

ELIG = Namespace("http://curam.cer.ontology/eligibility#")
SNAP = Namespace("http://curam.cer.ontology/snap#")

# Required classes from eligibility_core
REQUIRED_CLASSES = [
    "Applicant",
    "Household",
    "HouseholdMember",
    "Program",
    "EligibilityPeriod",
    "EligibilityDecision",
    "EvidenceRecord",
    "IncomeEvidence",
    "ResidencyEvidence",
    "IdentityEvidence",
    "PolicyThreshold",
    "RuleExecution",
]

# Key datatype properties
REQUIRED_PROPERTIES = [
    "grossMonthlyIncome",
    "householdSize",
    "residencyState",
    "isIdentityVerified",
    "programCode",
    "administeredInState",
    "thresholdPercentFPL",
    "periodStartDate",
    "periodEndDate",
    "decisionStatus",
    "ruleId",
    "ruleResult",
    "ruleReason",
]

# SNAP household sizes 1-8
SNAP_HOUSEHOLD_SIZES = list(range(1, 9))


class OntologyValidator:
    """
    Validates ontology structure and content.

    Ensures all required classes, properties, and SNAP thresholds exist.
    """

    def __init__(self, ontology_path: Optional[Path] = None):
        """Initialize with optional ontology path."""
        self.loader = OntologyLoader(ontology_path)

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Run all validation checks.

        Returns:
            (is_valid, list of error messages)
        """
        errors: List[str] = []
        graph = self.loader.load()

        # Check classes — URI must appear somewhere in the graph
        for name in REQUIRED_CLASSES:
            uri = ELIG[name]
            found = any(
                s == uri or p == uri or o == uri
                for s, p, o in graph
            )
            if not found:
                errors.append(f"Class not found: elig:{name}")

        # Check properties — URI must appear somewhere in the graph
        for name in REQUIRED_PROPERTIES:
            uri = ELIG[name]
            found = any(
                s == uri or p == uri or o == uri
                for s, p, o in graph
            )
            if not found:
                errors.append(f"Property not found or unused: elig:{name}")

        # Check SNAP thresholds for sizes 1-8
        for size in SNAP_HOUSEHOLD_SIZES:
            threshold_uri = SNAP[f"SNAP_GrossIncomeTest_Size{size}"]
            limits = list(graph.objects(threshold_uri, ELIG.monthlyIncomeLimit))
            if not limits:
                errors.append(
                    f"SNAP gross income threshold for household size {size} not found"
                )

        if errors:
            logger.warning("Ontology validation failed: %s", errors)
            return False, errors

        logger.info("Ontology validation passed")
        return True, []
