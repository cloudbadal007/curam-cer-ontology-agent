# curam-cer-ontology-agent

**Agentic AI for government welfare eligibility determination using OWL ontology, MCP, and LangChain**

This project demonstrates how to migrate legacy Merative Cúram CER (Cúram Express Rules) into a modern Agentic AI architecture. It uses SNAP (Supplemental Nutrition Assistance Program) as the reference—a publicly documented US welfare program.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: LangChain Agent (Orchestration)                        │
│  - Eligibility assessment, batch processing, parallel run       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  Layer 4: MCP Server (Tool Interface)                          │
│  - assess_household_eligibility, check_period_eligibility, etc. │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  Layer 3: Ontology Reasoner (SPARQL)                            │
│  - Injects facts, queries thresholds, produces audit trail      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  Layer 2: OWL Ontology (Semantic Layer)                         │
│  - eligibility_core.ttl, snap_rules.ttl                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  Layer 1: Pydantic Models (Data)                                │
│  - Household, EligibilityDecision, Program                      │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/cloudbadal007/curam-cer-ontology-agent.git
cd curam-cer-ontology-agent
pip install -e ".[dev]"

# 2. Configure (optional)
cp .env.example .env
# Set OPENAI_API_KEY or ANTHROPIC_API_KEY if using LLM features

# 3. Run basic example
python examples/basic_eligibility_check.py

# 4. Run tests
pytest tests/ -v
```

## Prerequisites

- Python 3.11+
- OpenAI API key or Anthropic key (for agent with LLM)
- No API key needed for ontology-only evaluation

## Running the MCP Server

```bash
python -m curam_cer_agent.mcp.server
```

Server runs on `http://localhost:8080`. Health check: `GET /health`. MCP endpoint: `/mcp`.

## Running the Agent

```python
from curam_cer_agent.agent.eligibility_agent import CaseData, EligibilityAgent

agent = EligibilityAgent()
case = CaseData(
    household_id="H1",
    program_code="SNAP",
    household_size=3,
    gross_monthly_income=2500,
    state="CA",
    identity_verified=True,
)
decision = agent.assess(case)
print(decision.status)  # ELIGIBLE | INELIGIBLE | PENDING_VERIFICATION
```

## Example Output

```json
{
  "decision_id": "abc-123",
  "status": "ELIGIBLE",
  "program_code": "SNAP",
  "household_id": "H1",
  "explanation": "Household meets gross income test.",
  "rule_executions": [
    {"rule_id": "IDENTITY_VERIFICATION", "rule_result": true},
    {"rule_id": "GROSS_INCOME", "rule_result": true, "threshold_used": 2888}
  ],
  "requires_human_review": false
}
```

## Project Structure

```
curam-cer-ontology-agent/
├── ontology/           # OWL ontology (core + SNAP rules)
├── src/curam_cer_agent/
│   ├── ontology/       # Loader, reasoner, validator
│   ├── mcp/            # MCP server and tools
│   ├── agent/          # LangChain eligibility agent
│   ├── models/         # Pydantic models
│   └── utils/          # Config, audit
├── tests/
├── examples/
└── docs/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

## Author

**Pankaj Kumar**

- GitHub: https://github.com/cloudbadal007
- Medium: https://medium.com/@cloudpankaj
- Substack: https://badalaiworld.substack.com/
- X: https://x.com/CloudyPankaj
- YouTube: https://www.youtube.com/@TheCivicStack
- LinkedIn: https://www.linkedin.com/in/pankaj-kumar-551b52a/

---

*Reference article: [YOUR_MEDIUM_ARTICLE_URL]*
