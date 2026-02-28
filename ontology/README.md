# Eligibility Ontology

This directory contains the OWL ontology files for the curam-cer-ontology-agent project.

## Files

| File | Purpose |
|------|---------|
| `eligibility_core.ttl` | Core OWL classes and properties modeling Cúram CER concepts |
| `snap_rules.ttl` | SNAP-specific program instance and income thresholds (130% FPL) |
| `medicaid_rules.ttl` | Medicaid stub for future expansion |

## Design Notes

- **eligibility_core.ttl** defines: Applicant, Household, HouseholdMember, Program, EligibilityPeriod, EligibilityDecision, EvidenceRecord (and subclasses), PolicyThreshold, RuleExecution.
- **snap_rules.ttl** imports the core ontology and adds SNAP program instance plus FY2026 gross income limits (1–8 persons) based on USDA documentation.
- **medicaid_rules.ttl** is a placeholder; Medicaid rules are state-specific and would be extended per state.

## Namespaces

- `elig:` — http://curam.cer.ontology/eligibility#
- `snap:` — http://curam.cer.ontology/snap#
- `medicaid:` — http://curam.cer.ontology/medicaid#
