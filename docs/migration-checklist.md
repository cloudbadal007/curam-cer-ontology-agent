# Migration Checklist: Cúram CER to Ontology Agent

A 7-step checklist for migrating legacy eligibility rules to the ontology-agent architecture.

## Step 1: Extract Rules and Thresholds

**Command**: Review CER documentation and extract program rules, thresholds, and evidence requirements.

**Definition of done**: List of programs, threshold tables (e.g., income by household size), and required evidence types.

**Common pitfalls**: Outdated thresholds; missing edge cases.

**Est. effort**: 2–4 weeks (depending on program complexity).

---

## Step 2: Create OWL Ontology

**Command**: Add/modify `ontology/*.ttl` to model programs and thresholds.

```bash
# Validate after editing
python -c "from curam_cer_agent.ontology.validator import OntologyValidator; v=OntologyValidator(); ok,err=v.validate(); print('OK' if ok else err)"
```

**Definition of done**: OntologyValidator passes; SNAP thresholds loaded.

**Common pitfalls**: Incorrect URIs; missing imports.

**Est. effort**: 1–2 weeks.

---

## Step 3: Implement Reasoner Logic

**Command**: Extend `OntologyReasoner.assess_eligibility()` for new programs and rules.

```bash
pytest tests/unit/test_reasoner.py -v
```

**Definition of done**: All reasoner tests pass; audit trail includes expected rules.

**Common pitfalls**: Off-by-one on thresholds; wrong comparison operators.

**Est. effort**: 1–2 weeks.

---

## Step 4: Expose MCP Tools

**Command**: Add or extend MCP tools in `src/curam_cer_agent/mcp/tools.py` and `server.py`.

```bash
python -m curam_cer_agent.mcp.server
# In another terminal: test tools via MCP Inspector or client
```

**Definition of done**: Tools return structured output; audit logging works.

**Common pitfalls**: Input validation gaps; incorrect error handling.

**Est. effort**: 1 week.

---

## Step 5: Configure Agent

**Command**: Set LLM provider, model, and system prompt in `.env` and `prompts.py`.

**Definition of done**: Agent uses only ontology tools; no hallucinated eligibility.

**Common pitfalls**: Overly verbose prompts; model ignoring constraints.

**Est. effort**: 3–5 days.

---

## Step 6: Parallel Run Validation

**Command**: Run `EligibilityAgent.parallel_run()` on representative cases.

```python
from curam_cer_agent.agent.eligibility_agent import CaseData, EligibilityAgent
agent = EligibilityAgent()
result = agent.parallel_run(case)
assert result.agree, result.match_explanation
```

**Definition of done**: Agent and direct evaluation agree on 100% of test cases.

**Common pitfalls**: Differences due to rounding or state handling.

**Est. effort**: 1–2 weeks (iterative).

---

## Step 7: Production Deployment

**Command**: Deploy MCP server; integrate with case management; enable audit logging.

**Definition of done**: Production traffic flows through agent; audit trail is complete; human review triggered for PENDING_VERIFICATION.

**Common pitfalls**: Missing API keys; wrong ontology path in production.

**Est. effort**: 2–4 weeks (infrastructure-dependent).
