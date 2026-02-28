# Ontology Design

## Why OWL Over JSON Schema

- **Reasoning**: OWL supports classification and inference
- **Composition**: Import snap_rules, medicaid_rules into core
- **SPARQL**: Graph queries for thresholds and programs
- **Governance**: Versioned ontology files; changes auditable

## Class Hierarchy

```
EvidenceRecord
├── IncomeEvidence
├── ResidencyEvidence
└── IdentityEvidence
```

Core classes: Applicant, Household, HouseholdMember, Program, EligibilityPeriod, EligibilityDecision, PolicyThreshold, RuleExecution.

## SWRL vs SPARQL Approach

We use **SPARQL** for eligibility logic:

- SWRL rules require OWL reasoners (HermiT, Pellet) and can be harder to debug
- SPARQL is well-supported in rdflib; easy to inspect and test
- Logic lives in Python (OntologyReasoner) with SPARQL for threshold lookup
- Future: SWRL rules could be added for complex deductions

## Extending for New Programs

1. Create `program_rules.ttl` importing eligibility_core
2. Add Program instance and PolicyThreshold instances
3. Extend OntologyReasoner.assess_eligibility() for new program_code
4. Add program to get_applicable_programs and REQUIRED_EVIDENCE

## Updating Thresholds When Legislation Changes

1. Edit `ontology/snap_rules.ttl` (or program-specific file)
2. Update `monthlyIncomeLimit` literals for each household size
3. Run OntologyValidator to confirm structure
4. Run tests; update expected_decisions if needed
5. Deploy; no code changes required for threshold-only updates
