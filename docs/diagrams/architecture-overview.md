# Architecture Overview (ASCII)

```
                    ┌──────────────────────────────────────────┐
                    │         LangChain Eligibility Agent        │
                    │  assess | batch_assess | parallel_run      │
                    └─────────────────────┬──────────────────────┘
                                          │
                    ┌─────────────────────▼──────────────────────┐
                    │              MCP Server :8080              │
                    │  /health  |  /mcp (Streamable HTTP)         │
                    │  Tools: assess, check_period, explain, ...  │
                    └─────────────────────┬──────────────────────┘
                                          │
                    ┌─────────────────────▼──────────────────────┐
                    │           Ontology Reasoner (SPARQL)       │
                    │  Inject facts → Query thresholds → Audit    │
                    └─────────────────────┬──────────────────────┘
                                          │
                    ┌─────────────────────▼──────────────────────┐
                    │     OWL Ontology (Turtle)                   │
                    │  eligibility_core.ttl | snap_rules.ttl       │
                    │  Classes: Household, Program, Threshold      │
                    └─────────────────────┬──────────────────────┘
                                          │
                    ┌─────────────────────▼──────────────────────┐
                    │         Pydantic Models                     │
                    │  Household, EligibilityDecision, Program    │
                    └────────────────────────────────────────────┘
```
