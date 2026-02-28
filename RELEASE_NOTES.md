# Release Notes

## v1.0.0 (2026-02-23)

### What's Included

- **OWL Ontology**: Core eligibility model (eligibility_core.ttl) and SNAP rules (snap_rules.ttl) with FY2026 income thresholds
- **Ontology Stack**: Loader, reasoner (SPARQL), and validator
- **MCP Server**: Five tools — assess_household_eligibility, check_period_eligibility, explain_eligibility_decision, get_applicable_programs, validate_evidence_completeness
- **LangChain Agent**: EligibilityAgent with assess(), batch_assess(), and parallel_run() for validation
- **Pydantic Models**: Household, Applicant, EligibilityDecision, RuleExecution, Program, PolicyThreshold
- **Examples**: Basic check, period check, batch assessment, explain decision
- **Tests**: Unit and integration tests with 15+ synthetic cases
- **Documentation**: Architecture, ontology design, MCP guide, migration checklist

### Known Limitations

- Medicaid rules are a stub (state-specific expansion planned)
- Net income test (100% FPL) not fully implemented for SNAP
- No UI dashboard; CLI and API only
- Single-state SNAP thresholds (48 contiguous states); Alaska/Hawaii not modeled

### Roadmap (v1.1.0)

- Medicaid rules by state
- Multi-state SNAP (Alaska, Hawaii)
- Web UI dashboard for case workers
- Export to Cúram CER format for comparison
- Evidence verification workflow integration

### Breaking Changes

None — initial release.
