# Agent Guide

## EligibilityAgent

The LangChain-based agent orchestrates MCP tools for eligibility determination.

### assess(case: CaseData) -> EligibilityDecision

Assesses a single case. Uses ontology tools directly (no LLM for the determination itself) to avoid hallucination. Returns a structured EligibilityDecision.

### batch_assess(cases: list[CaseData]) -> list[EligibilityDecision]

Processes multiple cases. Useful for bulk screening.

### parallel_run(case: CaseData) -> ComparisonResult

Runs the same case through:

1. Agent (via assess)
2. Direct OntologyReasoner.assess_eligibility

Returns ComparisonResult with `agree` true/false. Use for validation before production.

## Configuration

- `LLM_PROVIDER`: openai | anthropic
- `LLM_MODEL`: gpt-4o | claude-sonnet-4-6
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`: Required for LLM-based flows

## System Prompt

The agent is instructed to:

- Use only ontology tools for decisions
- Never hallucinate eligibility
- Include full audit trail
- Set requires_human_review when status is PENDING_VERIFICATION
