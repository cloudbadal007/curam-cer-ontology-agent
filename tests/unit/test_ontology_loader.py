"""
Unit tests for OntologyLoader.

Verifies ontology loading, caching, and structure.
"""

import tempfile
from pathlib import Path

import pytest

from curam_cer_agent.ontology.loader import OntologyLoader


def test_ontology_loads_successfully() -> None:
    """Arrange: default paths. Act: load. Assert: graph is non-empty."""
    loader = OntologyLoader()
    graph = loader.load()
    assert len(list(graph)) > 0


def test_snap_rules_imported_correctly() -> None:
    """Arrange: loader. Act: load. Assert: SNAP program and thresholds exist."""
    loader = OntologyLoader()
    graph = loader.load()
    from rdflib import Namespace
    SNAP = Namespace("http://curam.cer.ontology/snap#")
    elig = Namespace("http://curam.cer.ontology/eligibility#")
    snap_prog = list(graph.subjects(elig.programCode, None))
    assert any("SNAP" in str(s) for s in snap_prog)
    # Check at least one threshold
    limits = list(graph.predicate_objects(SNAP.SNAP_GrossIncomeTest_Size1))
    assert len(limits) > 0


def test_household_size_thresholds_present() -> None:
    """Arrange: loader. Act: load. Assert: thresholds for sizes 1-8 exist."""
    loader = OntologyLoader()
    graph = loader.load()
    from rdflib import Namespace
    SNAP = Namespace("http://curam.cer.ontology/snap#")
    elig = Namespace("http://curam.cer.ontology/eligibility#")
    for size in range(1, 9):
        uri = SNAP[f"SNAP_GrossIncomeTest_Size{size}"]
        objs = list(graph.objects(uri, elig.monthlyIncomeLimit))
        assert len(objs) == 1, f"Size {size} threshold missing"


def test_ontology_classes_exist() -> None:
    """Arrange: loader. Act: load. Assert: all 12 core classes appear in graph."""
    loader = OntologyLoader()
    graph = loader.load()
    from rdflib import Namespace
    elig = Namespace("http://curam.cer.ontology/eligibility#")
    classes = [
        "Applicant", "Household", "HouseholdMember", "Program",
        "EligibilityPeriod", "EligibilityDecision", "EvidenceRecord",
        "IncomeEvidence", "ResidencyEvidence", "IdentityEvidence",
        "PolicyThreshold", "RuleExecution",
    ]
    for name in classes:
        uri = elig[name]
        found = any(s == uri or p == uri or o == uri for s, p, o in graph)
        assert found, f"Class elig:{name} not found"


def test_ontology_properties_exist() -> None:
    """Arrange: loader. Act: load. Assert: key properties appear in graph."""
    loader = OntologyLoader()
    graph = loader.load()
    from rdflib import Namespace
    elig = Namespace("http://curam.cer.ontology/eligibility#")
    props = [
        "grossMonthlyIncome", "householdSize", "residencyState",
        "isIdentityVerified", "programCode", "decisionStatus", "ruleId",
    ]
    for name in props:
        uri = elig[name]
        found = any(s == uri or p == uri or o == uri for s, p, o in graph)
        assert found, f"Property elig:{name} not found"


def test_invalid_ontology_path_raises_error() -> None:
    """Arrange: path to non-existent file. Act: load. Assert: FileNotFoundError."""
    loader = OntologyLoader(Path("/nonexistent/path/ontology.ttl"))
    with pytest.raises(FileNotFoundError):
        loader.load()


def test_ontology_caching_works() -> None:
    """Arrange: load once. Act: load again with use_cache. Assert: same graph id."""
    loader = OntologyLoader()
    g1 = loader.load(use_cache=True)
    g2 = loader.load(use_cache=True)
    assert g1 is g2
