# Architecture

## Why Ontology Instead of a Rules Engine

Traditional rules engines (e.g., Drools, IBM ODM) encode logic in proprietary formats. OWL ontologies provide:

- **Interoperability**: RDF/OWL are W3C standards; tools and reasoners are widely available
- **Semantic clarity**: Classes and properties model the domain explicitly
- **SPARQL**: Declarative querying; rules are expressed as graph patterns
- **Extensibility**: New programs (Medicaid, TANF) extend the core model without rewriting

## Why MCP Instead of Direct Function Calls

Model Context Protocol (MCP) decouples the AI agent from the tool implementation:

- **Standardization**: Any MCP client (Claude, Cursor, custom) can connect
- **Tool discovery**: Agents list and invoke tools dynamically
- **Portability**: Same tools work with different LLM backends
- **Auditability**: Tool calls are first-class protocol messages

## Why LangChain for Orchestration

LangChain provides:

- **Tool binding**: MCP tools become LangChain tools for the agent
- **Prompt management**: System prompts constrain the agent to ontology-only decisions
- **Structured output**: EligibilityDecision as Pydantic models
- **Batch and parallel patterns**: batch_assess, parallel_run for validation

## Parallel Run Validation

Before production deployment, run the same case through:

1. **Ontology agent**: LLM + MCP tools
2. **Direct evaluation**: OntologyReasoner.assess_eligibility() (no LLM)

If they agree, the agent is behaving correctly. If they differ, investigate prompt or tool usage. This mirrors Cúram’s parallel run concept for legacy migrations.

## Cúram CER Concepts Mapped

| CER Concept        | Ontology / Agent Mapping              |
|--------------------|--------------------------------------|
| Assessment         | assess_household_eligibility          |
| Period eligibility | check_period_eligibility             |
| Rule execution     | RuleExecution in audit trail         |
| Policy threshold   | PolicyThreshold in ontology          |
| Evidence           | EvidenceRecord, validate_evidence    |
